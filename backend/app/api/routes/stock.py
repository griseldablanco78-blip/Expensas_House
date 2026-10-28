"""Stock HTTP routes."""
from fastapi import APIRouter
from fastapi import HTTPException
from backend.app.api.schemas import StockItemModel
from backend.app.infrastructure.json_store import get_stock, add_or_update_stock_item, delete_stock_item, open_stock_unit, consume_stock_unit

router = APIRouter(tags=["stock"])


@router.get("/api/stock")
def api_get_stock():
    """Retorna todo el inventario con cantidades cerradas y en uso."""
    return get_stock()



@router.post("/api/stock")
def api_add_stock(item: StockItemModel):
    """Crea o actualiza un producto en el inventario."""
    saved = add_or_update_stock_item(item.model_dump())
    return {"status": "success", "item": saved}



@router.put("/api/stock/{item_id}")
def api_update_stock(item_id: str, item: StockItemModel):
    """Modifica un producto existente."""
    data = item.model_dump()
    data["id"] = item_id
    saved = add_or_update_stock_item(data)
    return {"status": "success", "item": saved}



@router.delete("/api/stock/{item_id}")
def api_delete_stock(item_id: str):
    """Elimina un producto del inventario."""
    ok = delete_stock_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "success", "message": "Producto eliminado"}



@router.post("/api/stock/{item_id}/open")
def api_open_stock_unit(item_id: str):
    """Pasa una unidad de cerrada (stock) a abierta (en uso)."""
    res = open_stock_unit(item_id)
    if not res:
        raise HTTPException(status_code=400, detail="No hay unidades cerradas para abrir")
    return {"status": "success", "item": res}



@router.post("/api/stock/{item_id}/consume")
def api_consume_stock_unit(item_id: str):
    """Termina o consume una unidad que estaba abierta."""
    res = consume_stock_unit(item_id)
    if not res:
        raise HTTPException(status_code=400, detail="No hay unidades abiertas para terminar")
    return {"status": "success", "item": res}
