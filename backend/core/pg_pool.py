"""
pg_pool.py — пул соединений PostgreSQL.

Заменяет прямые psycopg2.connect() во всех store-файлах.
Решает проблему "server closed the connection unexpectedly" при простое.
"""

import logging
import os
import threading
from typing import Optional

logger = logging.getLogger("padplus.pg_pool")

_available = False
try:
    import psycopg2
    from psycopg2 import pool as pg_pool
    _available = True
except Exception as e:
    logger.warning("PostgreSQL недоступен: %s", e)
    psycopg2 = None
    pg_pool = None


class PgPool:
    """Потокобезопасный пул соединений PostgreSQL."""

    def __init__(self, minconn: int = 1, maxconn: int = 5):
        self._pool: Optional[pg_pool.ThreadedConnectionPool] = None
        self._minconn = minconn
        self._maxconn = maxconn
        self._lock = threading.Lock()
        self._dsn: Optional[str] = None

    @property
    def available(self) -> bool:
        return _available

    def _resolve_dsn(self) -> str:
        from core.config_manager import get_database_url
        dsn = get_database_url()
        if dsn and dsn.startswith("postgresql"):
            return dsn
        env_url = os.environ.get("DATABASE_URL")
        if env_url and env_url.startswith("postgresql"):
            return env_url
        raise RuntimeError("Нет DATABASE_URL для PostgreSQL")

    def _ensure_pool(self):
        if self._pool is not None:
            return
        with self._lock:
            if self._pool is not None:
                return
            dsn = self._resolve_dsn()
            self._pool = pg_pool.ThreadedConnectionPool(
                self._minconn, self._maxconn, dsn,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=5,
            )
            logger.info("PostgreSQL pool создан: min=%d max=%d", self._minconn, self._maxconn)

    def get_conn(self):
        self._ensure_pool()
        try:
            return self._pool.getconn()
        except Exception as e:
            logger.warning("Ошибка получения соединения из пула: %s", e)
            raise

    def put_conn(self, conn):
        if self._pool is None:
            return
        try:
            self._pool.putconn(conn)
        except Exception as e:
            logger.warning("Ошибка возврата соединения в пул: %s", e)

    def close_all(self):
        with self._lock:
            if self._pool is not None:
                self._pool.closeall()
                self._pool = None
                logger.info("PostgreSQL pool закрыт")


_pool: Optional[PgPool] = None


def get_pool() -> PgPool:
    global _pool
    if _pool is None:
        _pool = PgPool()
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        _pool.close_all()
        _pool = None


def get_connection():
    """Получить соединение из пула (замена psycopg2.connect())."""
    if not _available:
        raise RuntimeError("PostgreSQL недоступен (psycopg2 не загружен)")
    pool = get_pool()
    return pool.get_conn()


def put_connection(conn):
    """Вернуть соединение в пул."""
    if not _available or conn is None:
        return
    pool = get_pool()
    pool.put_conn(conn)
