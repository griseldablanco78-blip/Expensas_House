"""Comprobantes privados: únicamente el servidor utiliza la clave de Supabase."""
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote
from backend.app.infrastructure.postgres import enabled


def request(method, path, content=None, content_type='image/jpeg'):
    base = os.environ['SUPABASE_URL'].rstrip('/')
    if not base.startswith('https://'):
        raise RuntimeError('Storage requiere HTTPS.')
    secret = os.getenv('SUPABASE_SECRET_KEY') or os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey':secret, 'Content-Type':content_type, 'x-upsert':'false'}
    if not secret.startswith('sb_secret_'):
        headers['Authorization'] = 'Bearer '+secret
    try:
        with urlopen(Request(base+'/storage/v1/'+path, data=content,
                             headers=headers, method=method), timeout=20) as response:
            return response.read(4_000_001)
    except HTTPError as error:
        if method == 'HEAD' and error.code == 400:
            # Storage omite el cuerpo en HEAD; GET permite distinguir 404 de autenticación.
            request('GET', path)
            return b''
        body = error.read(4096)
        try:
            missing = str(json.loads(body).get('statusCode')) == '404'
        except ValueError:
            missing = False
        if error.code == 404 or missing:
            raise FileNotFoundError('Imagen no encontrada.') from None
        raise RuntimeError('El almacenamiento privado no respondió correctamente.') from None


def object_path(key):
    return 'object/'+quote(os.getenv('SUPABASE_STORAGE_BUCKET','expensa-private'),safe='')+'/'+quote(key,safe='/')


def put(key, content):
    if len(content) > 3_500_000:
        raise ValueError('La imagen preparada supera 3,5 MB.')
    request('POST', object_path(key), content)


def get(key):
    content = request('GET', object_path(key))
    if len(content) > 4_000_000:
        raise RuntimeError('La imagen supera el límite permitido.')
    return content


def exists(key):
    try:
        request('HEAD',object_path(key))
        return True
    except FileNotFoundError:
        return False
