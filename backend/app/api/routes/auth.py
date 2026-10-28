"""Email/password registration, verification, recovery and revocable sessions."""
import os
import secrets
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from argon2.exceptions import VerificationError, InvalidHashError
from backend.app.core import security as sec

router = APIRouter(prefix='/api/auth', tags=['authentication'])
members_router = APIRouter(prefix='/api/members', tags=['members'], dependencies=[Depends(sec.require_admin)])


class EmailInput(BaseModel):
    email: str = Field(max_length=254)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return sec.account_name(value) if sec.password_only() else sec.email_address(value)


class Credentials(EmailInput):
    password: str = Field(min_length=1, max_length=128)


class Login(Credentials):
    client: Literal['web', 'android'] = 'web'


class Token(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class Reset(Token):
    password: str = Field(max_length=128)


class Membership(EmailInput):
    profile: Literal['1', '2', '3']


def rate(request, action, email=''):
    ip = request.client.host if request.client else 'unknown'
    sec.throttle(f'{action}:ip:{ip}', limit=30)
    if email:
        sec.throttle(f'{action}:email:{sec.digest(email)}', limit=8)


@router.post('/register')
def register(payload: Credentials, request: Request):
    if sec.password_only():
        if not sec.owner_ready():
            raise HTTPException(503, 'Primero creá la cuenta administradora desde el configurador local de esta PC.')
        rate(request, 'register', payload.email)
        sec.valid_password(payload.password)
        with sec.database() as db:
            existing = db.execute('SELECT id FROM users WHERE email=?', (payload.email,)).fetchone()
            if existing:
                raise HTTPException(409, 'Ese usuario ya está registrado. Elegí otro o iniciá sesión.')
            db.execute('INSERT INTO users VALUES (?, ?, ?, 1)',
                       (secrets.token_hex(16), payload.email, sec.HASHER.hash(payload.password)))
        return {'message': 'Cuenta creada. Iniciá sesión. La administradora debe asignarte permisos para acceder al hogar.'}
    if not sec.mail_ready():
        raise HTTPException(503, 'La administradora debe configurar el servicio de correo HTTPS antes de crear cuentas.')
    rate(request, 'register', payload.email)
    sec.valid_password(payload.password)
    with sec.database() as db:
        existing = db.execute('SELECT * FROM users WHERE email=?', (payload.email,)).fetchone()
        if not existing:
            user_id = secrets.token_hex(16)
            db.execute('INSERT INTO users VALUES (?, ?, ?, 0)',
                       (user_id, payload.email, sec.HASHER.hash(payload.password)))
            existing = {'id': user_id, 'email': payload.email, 'verified': False}
    if not existing['verified']:
        sec.send_token(existing, 'verify')
    return {'message': 'Si corresponde, recibirás un correo para verificar tu cuenta. Revisá también la carpeta de spam.'}


@router.get('/status')
def status():
    """Public setup information only; no account, sender or secret is exposed."""
    if sec.password_only():
        ready = sec.owner_ready()
        return {'registration_available': ready, 'message': 'Podés crear tu usuario y contraseña.' if ready else
                'Primero creá tu cuenta administradora en el configurador local de esta PC.'}
    ready = sec.mail_ready()
    missing = 'el envío de correo' if os.getenv('EXPENSA_PUBLIC_URL', '').startswith('https://') else 'el envío de correo y HTTPS'
    return {'registration_available': ready,
            'message': 'Podés crear tu cuenta y verificar el correo.' if ready else
                       f'El registro todavía no está habilitado: falta configurar {missing}. No hagas más intentos de registro por ahora.'}


@router.post('/resend-verification')
def resend(payload: EmailInput, request: Request):
    if sec.password_only():
        raise HTTPException(404, 'La verificación por correo está desactivada.')
    rate(request, 'verification', payload.email)
    with sec.database() as db:
        user = db.execute('SELECT * FROM users WHERE email=?', (payload.email,)).fetchone()
    if user and not user['verified']:
        sec.send_token(user, 'verify')
    return {'message': 'Si la cuenta necesita verificación, recibirá un nuevo correo.'}


@router.post('/verify')
def verify(payload: Reset, request: Request):
    if sec.password_only():
        raise HTTPException(404, 'La verificación por correo está desactivada.')
    rate(request, 'verify')
    sec.consume_token(payload.token, 'verify', sec.HASHER.hash(sec.valid_password(payload.password)))
    return {'message': 'Correo verificado. Ya podés iniciar sesión; el acceso al hogar depende de los permisos de la administradora.'}


@router.post('/login')
def login(payload: Login, request: Request, response: Response):
    rate(request, 'login', payload.email)
    with sec.database() as db:
        user = db.execute('SELECT * FROM users WHERE email=?', (payload.email,)).fetchone()
    try:
        valid = sec.HASHER.verify(user['password_hash'] if user else sec.DUMMY_HASH, payload.password)
    except (VerificationError, InvalidHashError):
        valid = False
    if not user or not valid or not user['verified']:
        raise HTTPException(401, 'Usuario o contraseña incorrectos, o cuenta deshabilitada.')
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with sec.database() as db:
        role = db.execute('SELECT role FROM memberships WHERE email=?', (user['email'],)).fetchone()
        db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
        db.execute('INSERT INTO sessions VALUES (?, ?, ?, ?)',
                   (sec.digest(token), user['id'], sec.digest(csrf), time.time()+28800))
    secure = request.url.scheme == 'https'
    response.set_cookie(sec.COOKIE, token, max_age=28800, httponly=True, secure=secure, samesite='strict', path='/')
    response.set_cookie('expensa_csrf', csrf, max_age=28800, secure=secure, samesite='strict', path='/')
    result = {'user': {'id': user['id'], 'email': user['email'], 'role': role['role'] if role else None}}
    if payload.client == 'android':
        result['access_token'] = token
    return result


@router.get('/me')
def me(request: Request):
    return {'user': sec.session_user(request)}


@router.post('/logout')
def logout(request: Request, response: Response):
    sec.session_user(request)
    authorization = request.headers.get('authorization', '')
    token = authorization[7:] if authorization.startswith('Bearer ') else request.cookies.get(sec.COOKIE, '')
    with sec.database() as db:
        db.execute('DELETE FROM sessions WHERE hash=?', (sec.digest(token),))
    response.delete_cookie(sec.COOKIE, path='/'); response.delete_cookie('expensa_csrf', path='/')
    return {'message': 'Sesión cerrada.'}


@router.post('/forgot-password')
def forgot_password(payload: EmailInput, request: Request):
    if sec.password_only():
        raise HTTPException(409, 'La recuperación por correo está desactivada. Contactá a la administradora de esta PC.')
    rate(request, 'reset', payload.email)
    with sec.database() as db:
        user = db.execute('SELECT * FROM users WHERE email=?', (payload.email,)).fetchone()
    if user and user['verified']:
        sec.send_token(user, 'reset')
    return {'message': 'Si corresponde, recibirás un correo para restablecer tu contraseña.'}


@router.post('/reset-password')
def reset_password(payload: Reset, request: Request):
    if sec.password_only():
        raise HTTPException(404, 'La recuperación por correo está desactivada.')
    rate(request, 'reset-confirm')
    sec.consume_token(payload.token, 'reset', sec.HASHER.hash(sec.valid_password(payload.password)))
    return {'message': 'Contraseña actualizada. Se cerraron las sesiones anteriores.'}


@members_router.get('')
def members():
    with sec.database() as db:
        return [dict(row) for row in db.execute('SELECT email, role FROM memberships ORDER BY email')]


@members_router.post('')
def grant(payload: Membership, request: Request):
    with sec.database() as db:
        existing = db.execute('SELECT role FROM memberships WHERE email=?', (payload.email,)).fetchone()
        if not existing and not (sec.password_only() and db.execute('SELECT 1 FROM users WHERE email=?', (payload.email,)).fetchone()):
            raise HTTPException(404, 'El usuario debe crear su cuenta antes de que puedas asignarle permisos.')
        if existing and existing['role'] == 'admin':
            raise HTTPException(409, 'Este formulario no permite modificar el acceso de la administradora.')
        db.execute('INSERT OR REPLACE INTO memberships VALUES (?, ?)', (payload.email, sec.PROFILE_ROLES[payload.profile]))
        db.execute('DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email=?)', (payload.email,))
    return {'message': 'Permiso asignado. El usuario ya puede iniciar sesión.'}


@members_router.delete('')
def revoke(payload: EmailInput):
    with sec.database() as db:
        role = db.execute('SELECT role FROM memberships WHERE email=?', (payload.email,)).fetchone()
        if role and role['role'] == 'admin':
            raise HTTPException(409, 'No se puede revocar la administradora desde este formulario.')
        db.execute('DELETE FROM memberships WHERE email=?', (payload.email,))
        db.execute('DELETE FROM invitations WHERE email=?', (payload.email,))
        db.execute('DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email=?)', (payload.email,))
    return {'message': 'Acceso revocado.'}


@members_router.post('/invitations')
def invite(payload: Membership, request: Request):
    if sec.password_only():
        raise HTTPException(409, 'Sin correo: pedile que cree su usuario y luego asignale permisos con Actualizar permiso.')
    rate(request, 'invite', payload.email)
    if not sec.mail_ready():
        raise HTTPException(503, 'Falta configurar el envío de correos y la URL pública HTTPS.')
    token = secrets.token_urlsafe(32)
    with sec.database() as db:
        member = db.execute('SELECT role FROM memberships WHERE email=?', (payload.email,)).fetchone()
        if member:
            raise HTTPException(409, 'Este correo ya tiene acceso. Usá Actualizar permiso para cambiar su perfil.')
        db.execute('DELETE FROM invitations WHERE email=?', (payload.email,))
        db.execute('INSERT INTO invitations VALUES (?, ?, ?, ?)',
                   (sec.digest(token), payload.email, sec.PROFILE_ROLES[payload.profile], time.time()+172800))
    try:
        sec.deliver_email(payload.email, token, 'invite')
    except Exception:
        with sec.database() as db:
            db.execute('DELETE FROM invitations WHERE hash=?', (sec.digest(token),))
        raise
    return {'message': 'Invitación enviada. El acceso se activará cuando el destinatario verifique su correo y la acepte.'}


@members_router.get('/invitations')
def pending_invitations():
    with sec.database() as db:
        return [dict(row) for row in db.execute('SELECT email, role, expires FROM invitations WHERE expires>? ORDER BY email', (time.time(),))]


@router.post('/accept-invitation')
def accept_invitation(payload: Token, request: Request):
    if sec.password_only():
        raise HTTPException(404, 'Las invitaciones por correo están desactivadas.')
    user = sec.session_user(request)
    rate(request, 'accept-invite', user['email'])
    with sec.database() as db:
        db.execute('BEGIN IMMEDIATE')
        invite = db.execute('SELECT * FROM invitations WHERE hash=? AND expires>?',
                            (sec.digest(payload.token), time.time())).fetchone()
        if not invite or invite['email'] != user['email']:
            raise HTTPException(400, 'Invitación no válida para este correo, vencida o ya utilizada.')
        member = db.execute('SELECT role FROM memberships WHERE email=?', (user['email'],)).fetchone()
        if member:
            raise HTTPException(409, 'Tu cuenta ya tiene acceso. La administradora debe cambiar el perfil desde Integrantes.')
        db.execute('INSERT INTO memberships VALUES (?, ?)', (user['email'], invite['role']))
        db.execute('DELETE FROM invitations WHERE hash=?', (sec.digest(payload.token),))
    return {'message':'Invitación aceptada.', 'user':{**user, 'role':invite['role']}}


class ChangePassword(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)


class LoginPasswordChange(EmailInput):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(max_length=128)


@router.post('/change-password-at-login')
def change_password_at_login(payload: LoginPasswordChange, request: Request, response: Response):
    rate(request, 'password-login', payload.email)
    sec.valid_password(payload.new_password)
    with sec.database() as db:
        db.execute('BEGIN IMMEDIATE')
        user = db.execute('SELECT * FROM users WHERE email=?', (payload.email,)).fetchone()
        try:
            valid = sec.HASHER.verify(user['password_hash'] if user else sec.DUMMY_HASH, payload.current_password)
        except (VerificationError, InvalidHashError):
            valid = False
        if not user or not valid or not user['verified']:
            raise HTTPException(401, 'Usuario o contraseña actual incorrectos.')
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (sec.HASHER.hash(payload.new_password), user['id']))
        db.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
        db.execute('DELETE FROM email_tokens WHERE user_id=?', (user['id'],))
    response.delete_cookie(sec.COOKIE, path='/')
    response.delete_cookie('expensa_csrf', path='/')
    return {'message': 'Contraseña actualizada. Ya podés iniciar sesión con la nueva.'}


@router.post('/change-password')
def change_password(payload: ChangePassword, request: Request, response: Response):
    user = sec.session_user(request)
    rate(request, 'change-password', user['email'])
    sec.valid_password(payload.new_password)
    with sec.database() as db:
        db.execute('BEGIN IMMEDIATE')
        stored = db.execute('SELECT password_hash FROM users WHERE id=?', (user['id'],)).fetchone()
        try:
            sec.HASHER.verify(stored['password_hash'], payload.current_password)
        except (VerificationError, InvalidHashError):
            raise HTTPException(401, 'La contraseña actual es incorrecta.')
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (sec.HASHER.hash(payload.new_password), user['id']))
        db.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
        db.execute('DELETE FROM email_tokens WHERE user_id=?', (user['id'],))
    response.delete_cookie(sec.COOKIE, path='/')
    response.delete_cookie('expensa_csrf', path='/')
    return {'message': 'Contraseña actualizada. Iniciá sesión con la nueva contraseña.'}
