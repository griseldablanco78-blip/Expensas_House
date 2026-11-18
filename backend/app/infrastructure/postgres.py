"""Adaptador PostgreSQL: transacciones breves y parámetros separados del SQL."""
from contextlib import contextmanager
import os


def enabled():
    return os.getenv('EXPENSA_STORAGE', 'postgres' if os.getenv('VERCEL') else 'local') == 'postgres'


class NamedRow(dict):
    def __getitem__(self, key):
        return tuple(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


def row_factory(cursor):
    names = [c.name for c in cursor.description] if cursor.description else []
    return lambda values: NamedRow(zip(names, values))


@contextmanager
def connection():
    import psycopg
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError('Falta configurar la conexión persistente del servidor.')
    with psycopg.connect(url, sslmode='require', connect_timeout=10,
                         prepare_threshold=None, row_factory=row_factory) as conn:
        with conn.transaction():
            conn.execute('SET LOCAL search_path TO expensa, public')
            conn.execute("SET LOCAL statement_timeout = '20s'")
            yield conn


class AuthConnection:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, parameters=()):
        normalized = query.strip().upper()
        if normalized == 'BEGIN IMMEDIATE':
            return self.conn.execute('SELECT pg_advisory_xact_lock(7159021)')
        if normalized.startswith('INSERT OR REPLACE INTO MEMBERSHIPS'):
            query = ('INSERT INTO memberships (email,role) VALUES (?,?) '
                     'ON CONFLICT (email) DO UPDATE SET role=EXCLUDED.role')
        return self.conn.execute(query.replace('?', '%s'), parameters)
