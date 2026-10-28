"""Session authentication and permissions for the current shared household."""
import hashlib
import os
import re
import secrets
import smtplib
import sqlite3
import ssl
import time
from contextlib import contextmanager
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException, Request
from dotenv import load_dotenv

from backend.app.core.paths import PROJECT_ROOT

AUTH_DB = PROJECT_ROOT / 'data' / 'accounts.sqlite3'
HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(24))
ROLES = {'admin', 'full_editor', 'full_viewer', 'inventory_viewer'}
PROFILE_ROLES = {'1': 'full_editor', '2': 'full_viewer', '3': 'inventory_viewer'}
COOKIE = 'expensa_session'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_only():
    return os.getenv('EXPENSA_AUTH_MODE', 'password') == 'password'


def account_name(value):
    value = str(value).strip().casefold()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.@-]{2,79}', value):
        raise ValueError('Usá un usuario de 3 a 80 caracteres: letras, números, punto, guion o @.')
    return value


def owner_ready():
    with database() as db:
        return db.execute("SELECT 1 FROM memberships WHERE role='admin'").fetchone() is not None


def email_address(value):
    value = str(value).strip().casefold()
    if len(value) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        raise ValueError('Ingresá un correo válido.')
    return value


@contextmanager
def database():
    Path(AUTH_DB).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(AUTH_DB, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript('''
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS memberships (
                email TEXT PRIMARY KEY, role TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS email_tokens (
                hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                purpose TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions (
                hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                csrf_hash TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS rate_events (key TEXT NOT NULL, at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS invitations (
                hash TEXT PRIMARY KEY, email TEXT NOT NULL, role TEXT NOT NULL,
                expires REAL NOT NULL);
        ''')
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def throttle(key, limit=8, seconds=900):
    now = time.time()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM rate_events WHERE at < ?', (now - 86400,))
        count = db.execute('SELECT COUNT(*) FROM rate_events WHERE key=? AND at>?',
                           (key, now-seconds)).fetchone()[0]
        if count >= limit:
            raise HTTPException(429, 'Demasiados intentos. Esperá unos minutos antes de volver a intentar.', headers={'Retry-After': str(seconds)})
        db.execute('INSERT INTO rate_events VALUES (?, ?)', (key, now))


def mail_ready():
    # Pick up the first local wizard setup without restarting the public tunnel.
    # Existing process settings are never silently replaced (credential rotation
    # still requires a deliberate server restart).
    load_dotenv(PROJECT_ROOT / '.env', override=False)
    public = urlsplit(os.getenv('EXPENSA_PUBLIC_URL', ''))
    return bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM')
                and public.scheme == 'https' and public.hostname
                and (not os.getenv('SMTP_USER') or os.getenv('SMTP_PASSWORD')))


def deliver_email(recipient, token, purpose):
    if not mail_ready():
        raise HTTPException(503, 'Falta configurar el servicio de correo y la URL pública HTTPS. Contactá a la administradora.')
    base = os.environ['EXPENSA_PUBLIC_URL'].rstrip('/')
    if not base.startswith('https://'):
        raise HTTPException(503, 'El enlace de verificación necesita una URL HTTPS.')
    message = EmailMessage()
    message['From'] = os.environ['SMTP_FROM']
    message['To'] = recipient
    subjects = {'verify': 'Verificá tu correo en Expensa House',
                'reset': 'Restablecer contraseña de Expensa House',
                'invite': 'Invitación a tu hogar en Expensa House'}
    message['Subject'] = subjects[purpose]
    message.set_content(f"Abrí este enlace en Expensa House: {base}/#{purpose}={token}\n"
                        f"También podés copiar este código en la app: {token}\n" +
                        ('Vence en 48 horas. Iniciá sesión o creá una cuenta y verificá este mismo correo antes de aceptar.\n'
                         if purpose == 'invite' else 'Vence en 30 minutos.\n') +
                        'Solo se puede usar una vez. Si no lo solicitaste, ignorá este correo.')
    host = os.environ['SMTP_HOST']
    mode = os.getenv('SMTP_MODE', 'starttls')
    port = int(os.getenv('SMTP_PORT', '465' if mode == 'ssl' else '587'))
    context = ssl.create_default_context()
    try:
        if mode == 'ssl':
            server = smtplib.SMTP_SSL(host, port, timeout=15, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
        with server:
            if mode != 'ssl':
                server.ehlo(); server.starttls(context=context); server.ehlo()
            if os.getenv('SMTP_USER'):
                server.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
            server.send_message(message)
    except (OSError, smtplib.SMTPException, KeyError) as exc:
        raise HTTPException(503, 'No se pudo enviar el correo. Intentá más tarde.') from exc


def send_token(user, purpose):
    token = secrets.token_urlsafe(32)
    with database() as db:
        db.execute('DELETE FROM email_tokens WHERE user_id=? AND purpose=?', (user['id'], purpose))
        db.execute('INSERT INTO email_tokens VALUES (?, ?, ?, ?)',
                   (digest(token), user['id'], purpose, time.time()+1800))
    try:
        deliver_email(user['email'], token, purpose)
    except Exception:
        with database() as db:
            db.execute('DELETE FROM email_tokens WHERE hash=?', (digest(token),))
        raise


def consume_token(token, purpose, password_hash=None):
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        record = db.execute('SELECT * FROM email_tokens WHERE hash=? AND purpose=? AND expires>?',
                            (digest(token), purpose, time.time())).fetchone()
        if not record:
            raise HTTPException(400, 'El código no es válido o venció. Solicitá otro correo.')
        db.execute('DELETE FROM email_tokens WHERE hash=?', (digest(token),))
        if purpose == 'verify':
            db.execute('UPDATE users SET verified=1, password_hash=? WHERE id=?', (password_hash, record['user_id']))
            user = db.execute('SELECT * FROM users WHERE id=?', (record['user_id'],)).fetchone()
            admin_email = os.getenv('EXPENSA_ADMIN_EMAIL', '').strip().casefold()
            if admin_email and user['email'] == admin_email:
                db.execute('INSERT OR REPLACE INTO memberships VALUES (?, ?)', (user['email'], 'admin'))
        else:
            db.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash, record['user_id']))
            db.execute('DELETE FROM sessions WHERE user_id=?', (record['user_id'],))
            db.execute('DELETE FROM email_tokens WHERE user_id=? AND purpose=?', (record['user_id'], 'reset'))


def valid_password(password):
    if not 15 <= len(password) <= 128:
        raise HTTPException(422, 'Usá una contraseña de entre 15 y 128 caracteres. Podés usar una frase larga.')
    return password


def session_user(request: Request):
    authorization = request.headers.get('authorization', '')
    bearer = authorization.startswith('Bearer ')
    token = authorization[7:] if bearer else request.cookies.get(COOKIE, '')
    if not token or len(token) > 200:
        raise HTTPException(401, 'Iniciá sesión para continuar.', headers={'WWW-Authenticate': 'Bearer'})
    with database() as db:
        record = db.execute('''SELECT users.id, users.email, users.verified, memberships.role,
            sessions.csrf_hash FROM sessions JOIN users ON users.id=sessions.user_id
            LEFT JOIN memberships ON memberships.email=users.email
            WHERE sessions.hash=? AND sessions.expires>?''', (digest(token), time.time())).fetchone()
    if not record or not record['verified']:
        raise HTTPException(401, 'La sesión venció. Iniciá sesión otra vez.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and not bearer:
        csrf = request.headers.get('x-csrf-token', '')
        if not secrets.compare_digest(digest(csrf), record['csrf_hash']):
            raise HTTPException(403, 'La sesión de esta página necesita actualizarse. Volvé a iniciar sesión.')
    return {'id': record['id'], 'email': record['email'], 'role': record['role']}


def require_member(request: Request):
    user = session_user(request)
    if user['role'] not in ROLES:
        raise HTTPException(403, 'La administradora todavía debe darte acceso al hogar.')
    path = request.url.path.rstrip('/')
    if user['role'] == 'inventory_viewer' and path not in ('/api/stock', '/api/shopping', '/api/sync', '/stock', '/productos_criticos'):
        raise HTTPException(403, 'Tu perfil permite consultar únicamente Stock y Lista de compras.')
    read_only_query = user['role'] == 'full_viewer' and path in ('/api/ai/chat', '/api/voice/transcribe')
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and user['role'] not in ('admin', 'full_editor') and not read_only_query:
        raise HTTPException(403, 'Tu perfil es de solo lectura; no permite modificar datos.')
    request.state.user = user
    return user


def require_admin(request: Request):
    user = session_user(request)
    if user['role'] != 'admin':
        raise HTTPException(403, 'Solo la administradora puede gestionar integrantes y permisos.')
    return user
