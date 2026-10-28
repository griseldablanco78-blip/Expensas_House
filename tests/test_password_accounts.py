import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.core import security as sec


class PasswordAccountsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        for item in (patch.object(sec, 'AUTH_DB', Path(directory.name) / 'accounts.sqlite3'),
                     patch.dict('os.environ', {'EXPENSA_AUTH_MODE': 'password',
                                              'EXPENSA_PUBLIC_URL': 'https://testserver'})):
            item.start()
            self.addCleanup(item.stop)
        self.mail = patch.object(sec, 'deliver_email', side_effect=AssertionError('Must not send mail')).start()
        self.addCleanup(patch.stopall)
        self.client = TestClient(create_app(), base_url='https://testserver')
        self.password = 'Una frase privada para probar 2026'

    def owner(self):
        with sec.database() as db:
            db.execute('INSERT INTO users VALUES (?, ?, ?, 1)', ('owner-id', 'grise', sec.HASHER.hash(self.password)))
            db.execute('INSERT INTO memberships VALUES (?, ?)', ('grise', 'admin'))

    def login(self, username='grise', password=None):
        response = self.client.post('/api/auth/login', json={
            'email': username, 'password': password or self.password, 'client': 'android'})
        self.assertEqual(response.status_code, 200, response.text)
        return {'Authorization': 'Bearer ' + response.json()['access_token']}

    def test_public_registration_cannot_claim_owner(self):
        response = self.client.post('/api/auth/register', json={'email': 'grise', 'password': self.password})
        self.assertEqual(response.status_code, 503)
        self.assertFalse(self.client.get('/api/auth/status').json()['registration_available'])
        with sec.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM users').fetchone()[0], 0)

    def test_register_without_mail_and_admin_grants_access(self):
        self.owner()
        admin = self.login()
        response = self.client.post('/api/auth/register', json={'email': 'Invitado', 'password': self.password})
        self.assertEqual(response.status_code, 200, response.text)
        guest = self.login('invitado')
        self.assertEqual(self.client.get('/api/stock', headers=guest).status_code, 403)
        granted = self.client.post('/api/members', headers=admin, json={'email': 'invitado', 'profile': '3'})
        self.assertEqual(granted.status_code, 200, granted.text)
        self.assertEqual(self.client.get('/api/auth/me', headers=guest).status_code, 401)
        guest = self.login('invitado')
        self.assertEqual(self.client.get('/api/budget', headers=guest).status_code, 403)
        self.assertEqual(self.client.post('/api/auth/register', json={'email': 'invitado', 'password': self.password}).status_code, 409)
        self.mail.assert_not_called()

    def test_password_change_requires_old_password_and_revokes_all_sessions(self):
        self.owner()
        first, second = self.login(), self.login()
        new_password = 'Una nueva frase privada para probar 2026'
        payload = {'current_password': 'incorrecta', 'new_password': new_password}
        self.assertEqual(self.client.post('/api/auth/change-password', headers=first, json=payload).status_code, 401)
        payload['current_password'] = self.password
        self.assertEqual(self.client.post('/api/auth/change-password', headers=first, json=payload).status_code, 200)
        for headers in (first, second):
            self.assertEqual(self.client.get('/api/auth/me', headers=headers).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/login', json={'email': 'grise', 'password': self.password}).status_code, 401)
        self.login(password=new_password)

    def test_email_verification_and_recovery_are_disabled(self):
        self.owner()
        for endpoint, payload in (
            ('verify', {'token': 'x' * 32, 'password': self.password}),
            ('reset-password', {'token': 'x' * 32, 'password': self.password}),
            ('forgot-password', {'email': 'grise'}),
            ('resend-verification', {'email': 'grise'})):
            self.assertIn(self.client.post('/api/auth/' + endpoint, json=payload).status_code, (404, 409))
        self.mail.assert_not_called()

    def test_password_change_from_login_has_no_automatic_session(self):
        self.owner()
        old = self.login()
        payload = {'email': 'grise', 'current_password': 'incorrecta', 'new_password': self.password + ' nueva'}
        self.assertEqual(self.client.post('/api/auth/change-password-at-login', json=payload).status_code, 401)
        payload['current_password'] = self.password
        response = self.client.post('/api/auth/change-password-at-login', json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn('access_token', response.json())
        self.assertEqual(self.client.get('/api/auth/me', headers=old).status_code, 401)
        self.login(password=payload['new_password'])
