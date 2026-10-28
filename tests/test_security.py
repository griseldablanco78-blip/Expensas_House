import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.core import security as sec
from data import db

REAL_DELIVER_EMAIL = sec.deliver_email


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.sent = []
        self.patches = [patch.object(sec, 'AUTH_DB', Path(self.directory.name) / 'accounts.sqlite3'),
                        patch.object(db, 'DB_FILE', str(Path(self.directory.name) / 'state.json')),
                        patch.object(db, 'export_to_legacy_formats'),
                        patch.object(sec, 'mail_ready', return_value=True),
                        patch.object(sec, 'deliver_email', side_effect=lambda email, token, purpose: self.sent.append((email, token, purpose))),
                        patch.dict('os.environ', {'EXPENSA_AUTH_MODE':'email', 'EXPENSA_ADMIN_EMAIL':'admin@example.test', 'EXPENSA_PUBLIC_URL':'https://testserver', 'EXPENSA_ALLOWED_ORIGINS':'https://testserver'})]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)
        self.app = create_app()
        self.client = TestClient(self.app, base_url='https://testserver')
        db.save_db({'stock': [{'id':'stock', 'name':'Leche', 'category':'Comestibles', 'stockQuantity':2}],
                    'shopping': [], 'offers': [], 'expenses':[{'id':'private', 'amount':2000, 'note':'Privado'}],
                    'user_prefs': {'id':0, 'monthlyBudget':10000, 'totalSpent':2000}})
        self.password = 'Una frase extensa de prueba 2026'

    def account(self, email='admin@example.test', profile=None):
        registration = self.client.post('/api/auth/register', json={'email':email, 'password':self.password})
        self.assertEqual(registration.status_code, 200, registration.text)
        code = self.sent[-1][1]
        self.assertNotIn(code, registration.text)
        verified = self.client.post('/api/auth/verify', json={'token':code, 'password':self.password})
        self.assertEqual(verified.status_code, 200, verified.text)
        if profile:
            with sec.database() as connection:
                connection.execute('INSERT OR REPLACE INTO memberships VALUES (?, ?)', (email, profile))
        response = self.client.post('/api/auth/login', json={'email':email, 'password':self.password, 'client':'android'})
        self.assertEqual(response.status_code, 200, response.text)
        return {'Authorization':'Bearer '+response.json()['access_token']}

    def test_no_anonymous_access_including_legacy_routes(self):
        for path in ('/api/stock', '/api/budget', '/api/expenses', '/api/sync', '/stock', '/offers', '/productos_criticos'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)

    def test_incomplete_setup_does_not_consume_registration_attempts(self):
        with patch.object(sec, 'mail_ready', return_value=False):
            for _ in range(10):
                response = self.client.post('/api/auth/register', json={'email':'new@example.test', 'password':self.password})
                self.assertEqual(response.status_code, 503)
            status = self.client.get('/api/auth/status')
            self.assertEqual(status.status_code, 200)
            self.assertFalse(status.json()['registration_available'])
        with sec.database() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM rate_events').fetchone()[0], 0)

    def test_public_setup_status_never_exposes_smtp_secrets(self):
        response = self.client.get('/api/auth/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {'registration_available', 'message'})

    def test_registration_verification_and_password_storage(self):
        self.client.post('/api/auth/register', json={'email':'ADMIN@example.test', 'password':self.password})
        denied = self.client.post('/api/auth/login', json={'email':'admin@example.test', 'password':self.password})
        self.assertEqual(denied.status_code, 401)
        token = self.sent[-1][1]
        payload = {'token':token, 'password':self.password}
        self.assertEqual(self.client.post('/api/auth/verify', json=payload).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/verify', json=payload).status_code, 400)
        with sec.database() as connection:
            user = connection.execute('SELECT * FROM users').fetchone()
            self.assertNotEqual(user['password_hash'], self.password)
            self.assertTrue(user['password_hash'].startswith('$argon2id$'))

    def test_verified_accounts_need_admin_assigned_membership(self):
        headers = self.account('unassigned@example.test')
        self.assertEqual(self.client.get('/api/auth/me', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/stock', headers=headers).status_code, 403)

    def test_read_only_account_cannot_write_but_can_read_finances(self):
        headers = self.account('reader@example.test', 'full_viewer')
        self.assertEqual(self.client.get('/api/budget', headers=headers).status_code, 200)
        response = self.client.post('/api/budget', headers=headers, json={'monthlyBudget':1})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(db.get_user_prefs()['monthlyBudget'], 10000)
        self.assertEqual(self.client.post('/api/ai/chat', headers=headers, json={'message':'2'}).status_code, 200)

    def test_inventory_profile_never_receives_financial_snapshot(self):
        headers = self.account('inventory@example.test', 'inventory_viewer')
        self.assertEqual(self.client.get('/api/budget', headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/api/expenses', headers=headers).status_code, 403)
        self.assertEqual(self.client.post('/api/ai/chat', headers=headers, json={'message':'2'}).status_code, 403)
        snapshot = self.client.get('/api/sync', headers=headers).json()['data']
        self.assertEqual(snapshot['expenses'], [])
        self.assertEqual(snapshot['user_prefs']['totalSpent'], 0)
        self.assertNotIn('Privado', str(snapshot))
        self.assertEqual(snapshot['stock'][0]['name'], 'Leche')

    def test_editor_cannot_manage_members(self):
        headers = self.account('editor@example.test', 'full_editor')
        self.assertEqual(self.client.get('/api/members', headers=headers).status_code, 403)
        self.assertEqual(self.client.post('/api/members', headers=headers, json={'email':'other@example.test', 'profile':'1'}).status_code, 403)

    def test_revocation_invalidates_existing_session(self):
        admin = self.account()
        reader = self.account('reader@example.test', 'full_viewer')
        self.assertEqual(self.client.delete('/api/members', headers=admin, params={}).status_code, 422)
        response = self.client.request('DELETE', '/api/members', headers=admin, json={'email':'reader@example.test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/stock', headers=reader).status_code, 401)

    def test_cookie_requires_csrf_and_uses_secure_flags(self):
        self.account()
        response = self.client.post('/api/auth/login', json={'email':'admin@example.test', 'password':self.password})
        cookies = response.headers.get_list('set-cookie')
        self.assertTrue(any('HttpOnly' in item and 'Secure' in item and 'SameSite=strict' in item for item in cookies))
        self.assertNotIn('access_token', response.json())
        self.assertEqual(self.client.post('/api/budget', json={'monthlyBudget':20000}).status_code, 403)
        csrf = self.client.cookies.get('expensa_csrf')
        self.assertEqual(self.client.post('/api/budget', headers={'X-CSRF-Token':csrf}, json={'monthlyBudget':20000}).status_code, 200)

    def test_password_reset_revokes_sessions_and_token_is_single_use(self):
        old = self.account()
        self.client.post('/api/auth/forgot-password', json={'email':'admin@example.test'})
        token = self.sent[-1][1]
        new_password = 'Otra frase segura totalmente distinta'
        payload = {'token':token, 'password':new_password}
        self.assertEqual(self.client.post('/api/auth/reset-password', json=payload).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/reset-password', json=payload).status_code, 400)
        self.assertEqual(self.client.get('/api/stock', headers=old).status_code, 401)

    def test_expired_email_token_cannot_be_used(self):
        self.client.post('/api/auth/register', json={'email':'expired@example.test', 'password':self.password})
        with sec.database() as connection:
            connection.execute('UPDATE email_tokens SET expires=0')
        self.assertEqual(self.client.post('/api/auth/verify', json={'token':self.sent[-1][1], 'password':self.password}).status_code, 400)

    def test_login_rate_is_limited(self):
        for _ in range(8):
            self.assertEqual(self.client.post('/api/auth/login', json={'email':'missing@example.test', 'password':self.password}).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/login', json={'email':'missing@example.test', 'password':self.password}).status_code, 429)

    def test_nonloopback_http_and_unapproved_origin_are_rejected(self):
        remote = TestClient(self.app, base_url='http://192.168.0.28', client=('192.168.0.50',1234))
        self.assertEqual(remote.get('/api/stock').status_code, 426)
        self.assertEqual(self.client.get('/api/auth/me', headers={'Origin':'https://attacker.example'}).status_code, 403)
        headers = self.client.get('/').headers
        self.assertEqual(headers['cache-control'], 'no-store')
        self.assertIn("script-src 'self'", headers['content-security-policy'])

    def test_invitation_requires_matching_verified_email_and_single_acceptance(self):
        admin = self.account()
        response = self.client.post('/api/members/invitations', headers=admin, json={'email':'guest@example.test', 'profile':'3'})
        self.assertEqual(response.status_code, 200, response.text)
        invitation = self.sent[-1][1]
        self.assertNotIn(invitation, response.text)
        with sec.database() as connection:
            self.assertIsNone(connection.execute('SELECT role FROM memberships WHERE email=?', ('guest@example.test',)).fetchone())
        wrong = self.account('different@example.test')
        self.assertEqual(self.client.post('/api/auth/accept-invitation', headers=wrong, json={'token':invitation}).status_code, 400)
        guest = self.account('guest@example.test')
        accepted = self.client.post('/api/auth/accept-invitation', headers=guest, json={'token':invitation})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()['user']['role'], 'inventory_viewer')
        self.assertEqual(self.client.post('/api/auth/accept-invitation', headers=guest, json={'token':invitation}).status_code, 400)
        self.assertEqual(self.client.get('/api/budget', headers=guest).status_code, 403)

    def test_revoking_pending_invitation_prevents_acceptance(self):
        admin = self.account()
        self.client.post('/api/members/invitations', headers=admin, json={'email':'guest@example.test', 'profile':'1'})
        invitation = self.sent[-1][1]
        self.client.request('DELETE', '/api/members', headers=admin, json={'email':'guest@example.test'})
        guest = self.account('guest@example.test')
        self.assertEqual(self.client.post('/api/auth/accept-invitation', headers=guest, json={'token':invitation}).status_code, 400)

    def test_mail_uses_tls_and_contains_correct_invitation_link(self):
        with patch.dict('os.environ', {'SMTP_HOST':'smtp.example.test', 'SMTP_FROM':'sender@example.test',
                                      'SMTP_MODE':'starttls', 'SMTP_PORT':'587', 'SMTP_USER':'sender@example.test',
                                      'SMTP_PASSWORD':'test-only'}), patch.object(sec.smtplib, 'SMTP') as smtp:
            REAL_DELIVER_EMAIL('guest@example.test', 'dummy-invite-code', 'invite')
            server = smtp.return_value
            server.starttls.assert_called_once()
            message = server.send_message.call_args.args[0]
            self.assertIn('#invite=dummy-invite-code', message.get_content())
            self.assertIn('48 horas', message.get_content())


if __name__ == '__main__':
    unittest.main()
