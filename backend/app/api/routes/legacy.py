"""Legacy HTTP routes."""
from fastapi import APIRouter
from backend.app.infrastructure.json_store import get_stock

router = APIRouter(tags=["legacy"])


@router.get("/stock")
def get_legacy_stock():
    """Retrocompatibilidad con endpoints anteriores de api.py."""
    return get_stock()



@router.get("/productos_criticos")
def get_legacy_productos_criticos():
    """Retrocompatibilidad con endpoints anteriores de api.py."""
    stock = get_stock()
    return [p for p in stock if p.get("stockQuantity", 0) <= 1]
