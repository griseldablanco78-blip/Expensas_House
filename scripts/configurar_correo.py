"""Interactive local setup. Never pass SMTP passwords through command arguments."""
import getpass
import json
import os
from pathlib import Path
import smtplib
import ssl
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import dotenv_values, set_key


def main():
    status_path = ROOT / '.runtime' / 'mail-setup-status.json'
    status_path.parent.mkdir(exist_ok=True)
    settings = dotenv_values(ROOT / '.env')
    print('EXPENSA HOUSE - CONFIGURAR ENVIO DE CORREOS')
    print('Esta ventana es local. La clave no se muestra y no se envia al chat.')
    print('Para Gmail, usa una contrasena de aplicacion; no tu contrasena habitual.')
    address = input(f"Correo remitente [{settings.get('EXPENSA_ADMIN_EMAIL', '')}]: ").strip() or settings.get('EXPENSA_ADMIN_EMAIL', '')
    host = input('Servidor SMTP [smtp.gmail.com]: ').strip() or 'smtp.gmail.com'
    port_text = input('Puerto SMTP [587]: ').strip() or '587'
    print(f'Se comprobara la conexion TLS a {host}:{port_text} para {address}.')
    password = getpass.getpass('Contrasena de aplicacion / credencial SMTP (oculta): ')
    if host.casefold() in ('smtp.gmail.com', 'smtp.googlemail.com'):
        password = ''.join(password.split())
    if not address or not password:
        print('Configuracion cancelada: no se guardaron credenciales.')
        return
    try:
        port = int(port_text)
        context = ssl.create_default_context()
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
        with server:
            if port != 465:
                server.ehlo(); server.starttls(context=context); server.ehlo()
            server.login(address, password)
    except (ValueError, OSError, smtplib.SMTPException):
        status_path.write_text(json.dumps({'ready': False}), encoding='utf-8')
        print('No se pudo autenticar con el proveedor. No se guardo la clave. Revisa la cuenta y la contrasena de aplicacion.')
        return
    env_path = ROOT / '.env'
    env_path.touch(exist_ok=True)
    for key, value in {'SMTP_HOST':host, 'SMTP_PORT':str(port),
                       'SMTP_MODE':'ssl' if port == 465 else 'starttls',
                       'SMTP_FROM':address, 'SMTP_USER':address, 'SMTP_PASSWORD':password}.items():
        set_key(str(env_path), key, value)
    password = ''
    status_path.write_text(json.dumps({'ready': True}), encoding='utf-8')
    print('Conexion SMTP comprobada y configuracion guardada en .env. No se envio ningun correo de prueba.')
    print('En la primera configuracion, actualiza la web para activar el registro. Si cambiaste credenciales anteriores, reinicia el servidor.')


if __name__ == '__main__':
    try:
        main()
    finally:
        input('Presiona Enter para cerrar esta ventana...')
