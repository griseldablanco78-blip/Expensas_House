"""Shopping HTTP routes."""
from fastapi import APIRouter
from typing import Dict, Any
from fastapi import HTTPException
from backend.app.api.schemas import ShoppingItemModel
from backend.app.infrastructure.json_store import get_shopping, add_shopping_item, update_shopping_item, move_shopping_to_stock, delete_shopping_item

router = APIRouter(tags=["shopping"])


@router.get("/api/shopping")
def api_get_shopping():
    """Retorna la lista de compras."""
    return get_shopping()



@router.post("/api/shopping")
def api_add_shopping(item: ShoppingItemModel):
    """Agrega un producto a la lista de compras."""
    saved = add_shopping_item(item.model_dump())
    return {"status": "success", "item": saved}



@router.put("/api/shopping/{item_id}")
def api_update_shopping(item_id: str, updates: Dict[str, Any]):
    """Actualiza cantidad o datos de un ítem de la lista."""
    res = update_shopping_item(item_id, updates)
    if not res:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return {"status": "success", "item": res}



@router.post("/api/shopping/{item_id}/toggle")
def api_toggle_shopping(item_id: str):
    """Marca o desmarca un producto como comprado."""
    items = get_shopping()
    item = next((x for x in items if x["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    new_checked = not item.get("checked", False)
    res = update_shopping_item(item_id, {"checked": new_checked})
    return {"status": "success", "item": res}



@router.post("/api/shopping/{item_id}/move-to-stock")
def api_move_to_stock(item_id: str):
    """Mueve un ítem de la lista de compras al inventario de la casa."""
    res = move_shopping_to_stock(item_id)
    if not res:
        raise HTTPException(status_code=404, detail="Ítem no encontrado en lista de compras")
    return {"status": "success", "stock_item": res}



@router.delete("/api/shopping/{item_id}")
def api_delete_shopping(item_id: str):
    """Elimina un ítem de la lista de compras."""
    ok = delete_shopping_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return {"status": "success", "message": "Ítem eliminado"}
