"""Run an isolated, persistent demonstration API on loopback. Never uses household databases."""
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root = Path(__file__).resolve().parents[1]
folder = root / '.runtime' / 'demo'
folder.mkdir(parents=True, exist_ok=True)
os.environ.update(EXPENSA_AUTH_MODE='password', EXPENSA_DEMO_MODE='1')
from backend.app.infrastructure import json_store as store
from backend.app.core import security
from backend.app.services import receipt_archive
store.DB_FILE = str(folder / 'state.json')
store.export_to_legacy_formats = lambda *args: None
security.AUTH_DB = folder / 'accounts.sqlite3'
receipt_archive.ARCHIVE_DIR = folder / 'receipts'
if not Path(store.DB_FILE).exists():
    store.save_db({'stock': [], 'shopping': [], 'offers': [], 'expenses': [],
                   'user_prefs': {'id':0, 'monthlyBudget':10000, 'totalSpent':0}})
from scripts.configurar_cuenta_prueba import provision
provision('qa_household', 'SoloParaQA_2026_SinDatosReales')
# An offline manager reserves administration; the public demonstration account cannot grant access.
with security.database() as connection:
    if not connection.execute("SELECT 1 FROM memberships WHERE role='admin'").fetchone():
        connection.execute('INSERT INTO users VALUES (?, ?, ?, 1)',
                           (secrets.token_hex(16), 'demo-manager', security.HASHER.hash(secrets.token_urlsafe(32))))
        connection.execute('INSERT INTO memberships VALUES (?, ?)', ('demo-manager', 'admin'))
from backend.app.main import create_app
import uvicorn
if __name__ == '__main__':
    uvicorn.run(create_app(), host='127.0.0.1', port=8002, proxy_headers=True, forwarded_allow_ips='127.0.0.1')
