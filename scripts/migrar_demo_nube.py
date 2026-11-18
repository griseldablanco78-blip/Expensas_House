"""Explicit, non-destructive migration of fictitious demo data to Supabase PostgreSQL/Storage."""
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
root = Path(__file__).resolve().parents[1]
load_dotenv(root / '.env.cloud', override=False)
from backend.app.infrastructure import postgres, cloud_storage


def migrate():
    if not postgres.enabled():
        raise SystemExit('Configurar EXPENSA_STORAGE=postgres en .env.cloud antes de migrar.')
    folder = root / '.runtime' / 'demo'
    state_file, auth_file = folder / 'state.json', folder / 'accounts.sqlite3'
    if not state_file.is_file() or not auth_file.is_file():
        raise SystemExit('No existe el entorno demo local esperado; no se usan datos personales como alternativa.')
    payload = json.loads(state_file.read_text(encoding='utf-8'))
    # Schema setup is explicit, never executed for every serverless request.
    # El esquema se aplica por separado con el rol de administracion.
    bucket = os.getenv('SUPABASE_STORAGE_BUCKET', 'expensa-private')
    base, key = os.environ['SUPABASE_URL'].rstrip('/'), (os.getenv('SUPABASE_SECRET_KEY') or os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    headers = {'apikey':key, 'Content-Type':'application/json'}
    if not key.startswith('sb_secret_'): headers['Authorization']='Bearer '+key
    from urllib.parse import quote
    try:
        with urlopen(Request(base+'/storage/v1/bucket/'+quote(bucket,safe=''),headers=headers),timeout=15) as response:
            existing = json.load(response)
            if existing.get('public'):
                raise SystemExit('El bucket existente es público: elegir uno privado antes de continuar.')
    except HTTPError as error:
        body = error.read(4096)
        try: missing = str(json.loads(body).get('statusCode')) == '404'
        except ValueError: missing = False
        if error.code != 404 and not missing: raise
        body = json.dumps({'id':bucket,'name':bucket,'public':False,'file_size_limit':3500000,
                           'allowed_mime_types':['image/jpeg']}).encode()
        with urlopen(Request(base+'/storage/v1/bucket',data=body,headers=headers,method='POST'),timeout=15): pass
    # Copy referenced images before recording their metadata. Unreferenced draft photos are not migrated.
    for expense in payload.get('expenses', []):
        identity = expense.get('receipt_image')
        if identity:
            from backend.app.services.receipt_archive import image_path
            image_path(identity)  # Validate the identifier.
            if not cloud_storage.exists('receipts/'+identity+'.jpg'):
                cloud_storage.put('receipts/'+identity+'.jpg',(folder/'receipts'/(identity+'.jpg')).read_bytes())
    from psycopg.types.json import Jsonb
    with sqlite3.connect('file:'+str(auth_file)+'?mode=ro', uri=True) as local, postgres.connection() as conn:
        for user in local.execute('SELECT id,email,password_hash,verified FROM users'):
            conn.execute('INSERT INTO users VALUES (%s,%s,%s,%s) ON CONFLICT (email) DO NOTHING', tuple(user))
        for member in local.execute('SELECT email,role FROM memberships'):
            conn.execute('INSERT INTO memberships VALUES (%s,%s) ON CONFLICT (email) DO NOTHING',tuple(member))
        created=conn.execute('INSERT INTO app_state (id,payload) VALUES (%s,%s) ON CONFLICT (id) DO NOTHING RETURNING id',
                            (os.getenv('EXPENSA_HOUSEHOLD_ID','demo'),Jsonb(payload))).fetchone()
    print('Migración completada. Estado:', 'creado' if created else 'existente conservado',
          '| No se copiaron sesiones ni se borraron archivos locales.')


if __name__ == '__main__':
    migrate()
