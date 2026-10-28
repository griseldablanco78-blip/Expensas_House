"""Apply a merged snapshot as one storage operation."""
from backend.app.infrastructure.json_store import DB_LOCK, load_db, save_db
from backend.app.services.snapshot_merge import merge_snapshot, SyncConflict


def synchronize(incoming, baseline=None):
    with DB_LOCK:
        state = merge_snapshot(load_db(), incoming, baseline)
        save_db(state)
        return {"status": "success", "message": "Sincronización completada", "data": state}
