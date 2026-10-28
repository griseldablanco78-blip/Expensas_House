"""Sync HTTP routes."""
from fastapi import APIRouter
from fastapi import HTTPException, Request
from backend.app.api.schemas import AndroidSyncPayload
from backend.app.infrastructure.json_store import load_db
from backend.app.services.synchronization import synchronize, SyncConflict

router = APIRouter(tags=["sync"])


@router.get("/api/sync")
def api_get_sync_state(request: Request):
    """Devuelve el estado compartido para inicializar una instalación Android vacía."""
    data = load_db()
    if request.state.user['role'] == 'inventory_viewer':
        data = {'stock': data['stock'], 'shopping': data['shopping'],
                'expenses': [], 'offers': [], 'user_prefs': {'id': 0, 'monthlyBudget': 0, 'totalSpent': 0}}
    return {"status": "success", "data": data}



@router.post("/api/sync")
def api_full_sync(payload: AndroidSyncPayload):
    """
    Recibe una instantánea completa de Android y la publica para la Web.
    """
    try:
        return synchronize(payload.model_dump(), payload.baseline)
    except SyncConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
