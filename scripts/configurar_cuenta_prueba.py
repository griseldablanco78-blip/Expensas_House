"""Provision a local test account; never runs automatically or via HTTP."""
import argparse
import getpass
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from backend.app.core import security as sec


def provision(username, password, allow_short_test_password=False):
    username = sec.account_name(username)
    if not allow_short_test_password:
        sec.valid_password(password)
    elif not 6 <= len(password) <= 128:
        raise ValueError('La clave temporal debe tener entre 6 y 128 caracteres.')
    password_hash = sec.HASHER.hash(password)
    with sec.database() as db:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute('SELECT id FROM users WHERE email=?', (username,)).fetchone()
        identity = existing['id'] if existing else secrets.token_hex(16)
        if existing:
            db.execute('UPDATE users SET password_hash=?, verified=1 WHERE id=?', (password_hash, identity))
            db.execute('DELETE FROM sessions WHERE user_id=?', (identity,))
            db.execute('DELETE FROM email_tokens WHERE user_id=?', (identity,))
        else:
            db.execute('INSERT INTO users VALUES (?, ?, ?, 1)', (identity, username, password_hash))
        db.execute('INSERT OR REPLACE INTO memberships VALUES (?, ?)', (username, 'full_editor'))
    return identity


def main():
    parser = argparse.ArgumentParser(description='Crear o actualizar una cuenta local de prueba con permisos de edicion.')
    parser.add_argument('--usuario', default='prueba1')
    parser.add_argument('--permitir-clave-corta-de-prueba', action='store_true')
    args = parser.parse_args()
    load_dotenv(sec.PROJECT_ROOT / '.env')
    password = getpass.getpass('Contrasena de prueba: ')
    provision(args.usuario, password, args.permitir_clave_corta_de_prueba)
    print('Cuenta de prueba configurada. No se modificaron otras cuentas.')


if __name__ == '__main__':
    main()
