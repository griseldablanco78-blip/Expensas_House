"""Compatibility checks for the migration of API and frontend modules."""
import re
import unittest

from fastapi.testclient import TestClient
from backend.app.main import app, create_app
from backend.app.core.paths import PROJECT_ROOT, WEB_FRONTEND_DIR


class ArchitectureCompatibility(unittest.TestCase):
    def test_legacy_entry_point_uses_same_application(self):
        from web.api import app as legacy_app
        self.assertIs(legacy_app, app)

    def test_storage_still_targets_existing_data_folder(self):
        from data import db
        from backend.app.infrastructure import json_store
        self.assertIs(db, json_store)
        self.assertEqual(json_store.DATA_DIR, PROJECT_ROOT / 'data')

    def test_new_app_instances_register_existing_api_contracts(self):
        paths = TestClient(create_app()).get('/openapi.json').json()['paths']
        for path, method in [('/api/stock', 'get'), ('/api/stock', 'post'),
                             ('/api/stock/{item_id}/consume', 'post'),
                             ('/api/shopping', 'get'), ('/api/budget', 'post'),
                             ('/api/expenses', 'post'), ('/api/offers/compare', 'get'),
                             ('/api/ai/chat', 'post'), ('/api/voice/transcribe', 'post'),
                             ('/api/sync', 'get'), ('/api/sync', 'post'),
                             ('/api/receipts/scan', 'post'), ('/api/receipts/confirm', 'post'),
                             ('/offers', 'get'), ('/stock', 'get')]:
            with self.subTest(path=path, method=method):
                self.assertIn(method, paths[path])

    def test_web_scripts_are_served_after_frontend_move(self):
        client = TestClient(app)
        home = client.get('/')
        self.assertEqual(home.status_code, 200)
        scripts = re.findall(r'<script src="([^"]+)"', home.text)
        self.assertGreaterEqual(len(scripts), 5)
        for script in scripts:
            with self.subTest(script=script):
                response = client.get(script)
                self.assertEqual(response.status_code, 200)
                self.assertIn('javascript', response.headers['content-type'])
        self.assertEqual(client.get('/static/css/style.css').status_code, 200)
        self.assertEqual(WEB_FRONTEND_DIR, PROJECT_ROOT / 'frontend' / 'web')


if __name__ == '__main__':
    unittest.main()
