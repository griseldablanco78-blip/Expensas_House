"""
Persistencia unificada de datos para Expensa House.
Sincroniza el inventario, compras, ofertas y presupuesto entre la Web y la App Android.
Exporta automáticamente a data/stock.json para retrocompatibilidad con dashboards existentes.
"""
import json
import os
import uuid
import time
import threading
from functools import wraps
from copy import deepcopy
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional

DB_LOCK = threading.RLock()


def locked(function):
    @wraps(function)
    def call(*args, **kwargs):
        with DB_LOCK:
            return function(*args, **kwargs)
    return call


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DB_FILE = str(DATA_DIR / "app_state.json")
STOCK_JSON = os.path.join(DATA_DIR, "stock.json")
STOCK_CSV = os.path.join(DATA_DIR, "stock.csv")
CSV_CLEAN = os.path.join(DATA_DIR, "inventario_movimientos_limpio.csv")

INITIAL_DATA = {
    "stock": [
        {"id": "stock-1", "name": "Leche entera", "brand": "La Serenísima", "category": "Comestibles", "stockQuantity": 1, "inUseCount": 1, "unit": "litro", "price": 1450.0},
        {"id": "stock-2", "name": "Arroz largo fino", "brand": "Molinos", "category": "Comestibles", "stockQuantity": 2, "inUseCount": 1, "unit": "kg", "price": 1280.0},
        {"id": "stock-3", "name": "Detergente para vajilla", "brand": "Ala", "category": "Limpieza", "stockQuantity": 1, "inUseCount": 1, "unit": "botella 750ml", "price": 2400.0},
        {"id": "stock-4", "name": "Jabón líquido para ropa", "brand": "Ariel", "category": "Limpieza", "stockQuantity": 0, "inUseCount": 1, "unit": "botella 3L", "price": 5900.0},
        {"id": "stock-5", "name": "Café molido", "brand": "La Virginia", "category": "Comestibles", "stockQuantity": 0, "inUseCount": 1, "unit": "paquete 500g", "price": 4850.0},
        {"id": "stock-6", "name": "Yerba mate suave", "brand": "Playadito", "category": "Comestibles", "stockQuantity": 2, "inUseCount": 1, "unit": "paquete 1kg", "price": 4200.0},
        {"id": "stock-7", "name": "Aceite de girasol", "brand": "Natura", "category": "Comestibles", "stockQuantity": 1, "inUseCount": 1, "unit": "botella 1.5L", "price": 2890.0},
        {"id": "stock-8", "name": "Papel higiénico 4 rollos", "brand": "Elite", "category": "Hogar", "stockQuantity": 3, "inUseCount": 0, "unit": "pack", "price": 3800.0},
        {"id": "stock-9", "name": "Pechuga de pollo", "brand": "Granja Tres Arroyos", "category": "Carnicería", "stockQuantity": 2, "inUseCount": 0, "unit": "kg", "price": 6400.0},
        {"id": "stock-10", "name": "Tomate redondo", "brand": "Fresco", "category": "Verdulería", "stockQuantity": 1, "inUseCount": 0, "unit": "kg", "price": 1900.0},
        {"id": "stock-11", "name": "Lavandina común", "brand": "Ayudín", "category": "Limpieza", "stockQuantity": 2, "inUseCount": 1, "unit": "botella 1L", "price": 1650.0},
        {"id": "stock-12", "name": "Fideos tallarines", "brand": "Matarazzo", "category": "Comestibles", "stockQuantity": 3, "inUseCount": 0, "unit": "paquete 500g", "price": 1390.0}
    ],
    "shopping": [
        {"id": "shop-1", "name": "Jabón líquido para ropa", "brand": "Ariel", "category": "Limpieza", "detail": "Reposición automática (stock crítico)", "quantity": 1, "suggestedStore": "Carrefour", "checked": False},
        {"id": "shop-2", "name": "Café molido", "brand": "La Virginia", "category": "Comestibles", "detail": "Reposición automática (sin stock)", "quantity": 1, "suggestedStore": "Día", "checked": False},
        {"id": "shop-3", "name": "Leche entera", "brand": "La Serenísima", "category": "Comestibles", "detail": "Consumo habitual", "quantity": 3, "suggestedStore": "Coto", "checked": False}
    ],
    "user_prefs": {
        "id": 0,
        "monthlyBudget": 180000.0,
        "totalSpent": 74500.0
    },
    "expenses": [
        {"id": "exp-1", "category": "Comestibles", "amount": 34500.0, "timestamp": int(time.time() * 1000) - 86400000 * 3, "note": "Compra semanal súper"},
        {"id": "exp-2", "category": "Limpieza", "amount": 18200.0, "timestamp": int(time.time() * 1000) - 86400000 * 5, "note": "Artículos de limpieza"},
        {"id": "exp-3", "category": "Carnicería", "amount": 21800.0, "timestamp": int(time.time() * 1000) - 86400000 * 7, "note": "Carne y pollo del mes"}
    ],
    "offers": [
        {"id": "off-1", "store": "Coto", "product": "Leche La Serenísima 1L", "brand": "La Serenísima", "price": "$1.390", "saving": "2do al 70%", "isExternal": True},
        {"id": "off-2", "store": "Carrefour", "product": "Jabón Líquido Ariel 3L", "brand": "Ariel", "price": "$5.490", "saving": "20% off", "isExternal": True},
        {"id": "off-3", "store": "Día", "product": "Café La Virginia 500g", "brand": "La Virginia", "price": "$4.250", "saving": "3x2 Club Día", "isExternal": True}
    ],
    "last_sync": int(time.time() * 1000)
}

@locked
def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        save_db(deepcopy(INITIAL_DATA))
        return deepcopy(INITIAL_DATA)
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure keys exist
            for key in ["stock", "shopping", "user_prefs", "expenses", "offers"]:
                if key not in data:
                    data[key] = deepcopy(INITIAL_DATA.get(key, []))
            return data
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("No se pudo leer app_state.json; se conserva el archivo para recuperación.") from exc

@locked
def save_db(data: Dict[str, Any]):
    data["last_sync"] = int(time.time() * 1000)
    temporary = DB_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temporary, DB_FILE)
    export_to_legacy_formats(data)

@locked
def export_to_legacy_formats(data: Dict[str, Any]):
    """Exporta a data/stock.json y data/stock.csv para compatibilidad total con dashboard.py."""
    try:
        stock_items = data.get("stock", [])
        legacy_list = []
        for item in stock_items:
            legacy_list.append({
                "name": item.get("name", "Producto"),
                "brand": item.get("brand", "Genérica"),
                "category": item.get("category", "Comestibles"),
                "stockQuantity": int(item.get("stockQuantity", 0)),
                "inUseCount": int(item.get("inUseCount", 0)),
                "price": float(item.get("price", 0.0)),
                "unit": item.get("unit", "unidad")
            })
        with open(STOCK_JSON, "w", encoding="utf-8") as f:
            json.dump(legacy_list, f, ensure_ascii=False, indent=2)
            
        df = pd.DataFrame(legacy_list)
        df.to_csv(STOCK_CSV, index=False)
    except Exception as e:
        print(f"Error exportando formatos legacy: {e}")

# Funciones de acceso rápido
@locked
def get_stock() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("stock", [])

@locked
def add_or_update_stock_item(item: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    if not item.get("id"):
        item["id"] = str(uuid.uuid4())
    
    # Check if exists
    existing_idx = next((i for i, x in enumerate(db["stock"]) if x["id"] == item["id"]), None)
    if existing_idx is not None:
        db["stock"][existing_idx].update(item)
        saved_item = db["stock"][existing_idx]
    else:
        db["stock"].append(item)
        saved_item = item
        
    # Auto-sync with shopping list if critical
    check_and_sync_shopping_for_stock(db, saved_item)
    save_db(db)
    return saved_item

@locked
def check_and_sync_shopping_for_stock(db: Dict[str, Any], stock_item: Dict[str, Any]):
    stock_qty = stock_item.get("stockQuantity", 0)
    name = stock_item.get("name", "").strip().lower()
    
    if stock_qty <= 1:
        # Check if already in shopping
        exists = any(s.get("name", "").strip().lower() == name for s in db["shopping"])
        if not exists:
            db["shopping"].append({
                "id": str(uuid.uuid4()),
                "name": stock_item.get("name"),
                "brand": stock_item.get("brand", "Genérica"),
                "category": stock_item.get("category", "Comestibles"),
                "detail": "Reposición automática (stock crítico)",
                "quantity": 1,
                "suggestedStore": None,
                "checked": False
            })

@locked
def delete_stock_item(item_id: str) -> bool:
    db = load_db()
    original_len = len(db["stock"])
    db["stock"] = [x for x in db["stock"] if x["id"] != item_id]
    if len(db["stock"]) < original_len:
        save_db(db)
        return True
    return False

@locked
def open_stock_unit(item_id: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    for item in db["stock"]:
        if item["id"] == item_id:
            if item.get("stockQuantity", 0) > 0:
                item["stockQuantity"] = item["stockQuantity"] - 1
                item["inUseCount"] = item.get("inUseCount", 0) + 1
                check_and_sync_shopping_for_stock(db, item)
                save_db(db)
                return item
    return None

@locked
def consume_stock_unit(item_id: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    for item in db["stock"]:
        if item["id"] == item_id:
            if item.get("inUseCount", 0) > 0:
                item["inUseCount"] = item["inUseCount"] - 1
                save_db(db)
                return item
    return None

@locked
def get_shopping() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("shopping", [])

@locked
def add_shopping_item(item: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    if not item.get("id"):
        item["id"] = str(uuid.uuid4())
    db["shopping"].append(item)
    save_db(db)
    return item

@locked
def update_shopping_item(item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = load_db()
    for item in db["shopping"]:
        if item["id"] == item_id:
            item.update(updates)
            save_db(db)
            return item
    return None

@locked
def delete_shopping_item(item_id: str) -> bool:
    db = load_db()
    original_len = len(db["shopping"])
    db["shopping"] = [x for x in db["shopping"] if x["id"] != item_id]
    if len(db["shopping"]) < original_len:
        save_db(db)
        return True
    return False

@locked
def move_shopping_to_stock(item_id: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    shop_item = next((x for x in db["shopping"] if x["id"] == item_id), None)
    if not shop_item:
        return None
    
    # Check if item exists in stock
    name = shop_item.get("name", "").strip().lower()
    brand = shop_item.get("brand", "").strip().lower()
    qty = shop_item.get("quantity", 1)
    
    existing = next((s for s in db["stock"] if s.get("name", "").strip().lower() == name and s.get("brand", "").strip().lower() == brand), None)
    if existing:
        existing["stockQuantity"] = existing.get("stockQuantity", 0) + qty
        result_stock = existing
    else:
        new_item = {
            "id": str(uuid.uuid4()),
            "name": shop_item.get("name"),
            "brand": shop_item.get("brand", "Genérica"),
            "category": shop_item.get("category", "Comestibles"),
            "stockQuantity": qty,
            "inUseCount": 0,
            "unit": "unidad",
            "price": 0.0
        }
        db["stock"].append(new_item)
        result_stock = new_item
        
    db["shopping"] = [x for x in db["shopping"] if x["id"] != item_id]
    save_db(db)
    return result_stock

@locked
def get_user_prefs() -> Dict[str, Any]:
    db = load_db()
    return db.get("user_prefs", {"monthlyBudget": 0.0, "totalSpent": 0.0})

@locked
def update_user_prefs(prefs: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    db["user_prefs"].update(prefs)
    save_db(db)
    return db["user_prefs"]

@locked
def get_expenses() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("expenses", [])

@locked
def add_expense(expense: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    if not expense.get("id"):
        expense["id"] = str(uuid.uuid4())
    if not expense.get("timestamp"):
        expense["timestamp"] = int(time.time() * 1000)
    db["expenses"].insert(0, expense)
    
    # Actualizar totalSpent en user_prefs
    db["user_prefs"]["totalSpent"] = db["user_prefs"].get("totalSpent", 0.0) + expense.get("amount", 0.0)
    save_db(db)
    return expense

@locked
def get_offers() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("offers", [])

@locked
def add_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    if not offer.get("id"):
        offer["id"] = str(uuid.uuid4())
    db["offers"].insert(0, offer)
    save_db(db)
    return offer

# Inicializar exportación al importar
load_db()
