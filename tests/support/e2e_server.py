"""Loopback-only real API with disposable accounts and household state for browser tests."""
import os
import sys
import tempfile
from pathlib import Path
if os.getenv('EXPENSA_E2E') != '1':
    raise SystemExit('Only run through the isolated Playwright configuration.')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.update(EXPENSA_AUTH_MODE='password', EXPENSA_PUBLIC_URL='http://127.0.0.1:18765',
                  EXPENSA_ALLOWED_ORIGINS='http://127.0.0.1:18765', RATONEANDO_API_URL='')
from backend.app.infrastructure import json_store as store
from backend.app.core import security
from backend.app.services import receipt_archive
import uvicorn
with tempfile.TemporaryDirectory(prefix='expensa-e2e-') as directory:
    root = Path(directory)
    store.DB_FILE = str(root / 'state.json')
    store.export_to_legacy_formats = lambda *args: None
    security.AUTH_DB = root / 'accounts.sqlite3'
    receipt_archive.ARCHIVE_DIR = root / 'receipts'
    store.save_db({'stock':[], 'shopping':[], 'offers':[], 'expenses':[],
                   'user_prefs':{'id':0,'monthlyBudget':10000,'totalSpent':0}})
    with security.database() as connection:
        connection.execute('INSERT INTO users VALUES (?, ?, ?, 1)',
                           ('qa-owner','qa-owner',security.HASHER.hash('Solo para pruebas locales 2026')))
        connection.execute('INSERT INTO memberships VALUES (?, ?)', ('qa-owner','admin'))
    from backend.app.main import create_app
    uvicorn.run(create_app(), host='127.0.0.1', port=18765)
