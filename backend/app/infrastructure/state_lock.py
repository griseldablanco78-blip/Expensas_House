"""Bloqueo reentrante local y transacción entre instancias de Vercel."""
import threading
from backend.app.infrastructure import postgres


class StateLock:
    def __init__(self):
        self.lock = threading.RLock()
        self.local = threading.local()

    @property
    def connection(self):
        return self.local.conn

    def __enter__(self):
        self.lock.acquire()
        depth = getattr(self.local, 'depth', 0)
        try:
            if not depth and postgres.enabled():
                self.local.context = postgres.connection()
                self.local.conn = self.local.context.__enter__()
                try:
                    self.local.conn.execute('SELECT pg_advisory_xact_lock(7159022)')
                except BaseException:
                    import sys
                    self.local.context.__exit__(*sys.exc_info())
                    raise
            self.local.depth = depth + 1
            return self
        except BaseException:
            self.lock.release()
            raise

    def __exit__(self, *error):
        self.local.depth -= 1
        try:
            if not self.local.depth and postgres.enabled():
                self.local.context.__exit__(*error)
                self.local.conn = None
        finally:
            self.lock.release()
