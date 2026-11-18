"""Pruebas explícitas contra el hogar ficticio; nunca se ejecutan por defecto."""
import os
import time
from concurrent.futures import ThreadPoolExecutor
import pytest

pytestmark = pytest.mark.skipif(os.getenv('EXPENSA_CLOUD_TEST') != '1', reason='Requiere entorno ficticio PostgreSQL autorizado')


def test_cloud_transactions_rollback_and_serialize_between_instances(monkeypatch):
    from dotenv import dotenv_values
    from backend.app.infrastructure import postgres
    from backend.app.infrastructure.state_lock import StateLock
    from psycopg.types.json import Jsonb
    settings = dotenv_values('.env.cloud')
    for key, value in settings.items():
        if value is not None:
            monkeypatch.setenv(key,value)
    assert os.getenv('EXPENSA_DEMO_MODE') == '1'
    marker = '_regression_counter'
    with postgres.connection() as conn:
        assert conn.execute('SELECT current_user').fetchone()[0] == 'expensa_server'
    # Un fallo debe deshacer incluso una escritura ya enviada a PostgreSQL.
    with pytest.raises(ValueError):
        with StateLock() as lock:
            lock.connection.execute("UPDATE app_state SET payload=jsonb_set(payload,%s,%s) WHERE id='demo'", ([marker],Jsonb(-1)))
            raise ValueError('Rollback de prueba')
    with postgres.connection() as conn:
        assert marker not in conn.execute("SELECT payload FROM app_state WHERE id='demo'").fetchone()[0]

    def increment(_):
        # Instancias distintas: el bloqueo de Python no puede serializarlas.
        with StateLock() as lock:
            state = lock.connection.execute("SELECT payload FROM app_state WHERE id='demo'").fetchone()[0]
            state[marker] = state.get(marker,0)+1
            time.sleep(.05)
            lock.connection.execute("UPDATE app_state SET payload=%s WHERE id='demo'",(Jsonb(state),))
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(increment,range(4)))
        with postgres.connection() as conn:
            assert conn.execute("SELECT payload FROM app_state WHERE id='demo'").fetchone()[0][marker] == 4
    finally:
        with StateLock() as lock:
            lock.connection.execute("UPDATE app_state SET payload=payload-%s WHERE id='demo'",(marker,))
