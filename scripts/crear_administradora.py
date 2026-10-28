"""Local owner provisioning; never available as a public HTTP endpoint."""
import getpass
import secrets
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from backend.app.core import security as sec
load_dotenv(sec.PROJECT_ROOT / '.env')


def main():
    print('EXPENSA HOUSE - CREAR ADMINISTRADORA LOCAL')
    print('No conecta Gmail. Elegi tu usuario y una frase de al menos 15 caracteres.')
    if sec.owner_ready():
        print('Ya existe una administradora. No se cambiaron cuentas ni contrasenas.')
        return
    username = sec.account_name(input('Nombre de usuario: '))
    password = getpass.getpass('Tu nueva contrasena (no se vera): ')
    confirmation = getpass.getpass('Repeti la contrasena: ')
    if password != confirmation:
        raise ValueError('Las contrasenas no coinciden. No se guardo la cuenta.')
    sec.valid_password(password)
    password_hash = sec.HASHER.hash(password)
    with sec.database() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute("SELECT 1 FROM memberships WHERE role='admin'").fetchone():
            raise ValueError('Ya existe una administradora.')
        if db.execute('SELECT 1 FROM users WHERE email=?', (username,)).fetchone():
            raise ValueError('Ese usuario ya existe. No se modifico su contrasena. Elegi otro usuario.')
        db.execute('INSERT INTO users VALUES (?, ?, ?, 1)', (secrets.token_hex(16), username, password_hash))
        db.execute('INSERT INTO memberships VALUES (?, ?)', (username, 'admin'))
    print('Cuenta administradora creada. Ya podes iniciar sesion con tu usuario y contrasena.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        from fastapi import HTTPException
        print(error.detail if isinstance(error, HTTPException) else str(error))
    finally:
        input('Presiona Enter para cerrar...')
