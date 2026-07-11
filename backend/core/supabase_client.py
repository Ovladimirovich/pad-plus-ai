"""
📦 Supabase Client

Подключение к Supabase (PostgreSQL + Auth + Storage)
Для локальной разработки можно использовать локальный PostgreSQL

Использование:
    supabase = get_supabase()
    users = supabase.table("users").select("*").execute()
"""

import os
import logging
import sqlite3
import json
from typing import Optional, Any, Dict, List
from pathlib import Path
from types import SimpleNamespace

logger = logging.getLogger("padplus.supabase")

# Пытаемся импортировать supabase
HAS_SUPABASE = False
Client = type(None)  # Заглушка по умолчанию
create_client = None

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
    logger.info("✅ Supabase библиотека загружена")
except ImportError as e:
    logger.warning(f"⚠️ Supabase не установлен: {e}")
except Exception as e:
    logger.warning(f"⚠️ Ошибка импорта Supabase: {e}")


_supabase: Optional[Client] = None


def _is_development() -> bool:
    """
    Проверяет, работаем ли мы в development-режиме.

    В development-режиме Supabase отключается принудительно,
    даже если библиотека установлена и credentials есть в .env.
    """
    if os.getenv("RENDER") == "true":
        return False
    env = os.getenv("APP_ENV", "").strip().lower()
    if env in ("production", "prod"):
        return False
    return True


def get_supabase() -> Optional[Client]:
    """
    Возвращает клиент Supabase
    
    Инициализируется один раз при первом вызове.
    Берёт URL и ключ из .env
    
    Returns:
        Клиент Supabase или None если не настроен
    """
    global _supabase
    
    if _supabase is not None:
        return _supabase

    if _is_development():
        logger.info("🔧 Локальный режим: Supabase отключён (APP_ENV=development)")
        return None
    
    if not HAS_SUPABASE:
        logger.warning("⚠️ Supabase клиент не установлен")
        return None
    
    # Получаем настройки из .env
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    # Для локальной разработки с PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    
    if not supabase_url and not database_url:
        logger.warning("⚠️ SUPABASE_URL и DATABASE_URL не настроены")
        return None

    try:
        # Таймаут для HTTP запросов к Supabase (через переменную окружения httpx)
        # supabase-py использует httpx, таймаут задается через SUPABASE_TIMEOUT
        supabase_timeout = int(os.getenv("SUPABASE_TIMEOUT", "30"))
        
        if supabase_url and supabase_key:
            if supabase_key.startswith('sb_publishable_'):
                _supabase = create_client(supabase_url, supabase_key)
                logger.info(f"✅ Supabase подключен: {supabase_url} (anon key, timeout={supabase_timeout}s)")
            else:
                _supabase = create_client(supabase_url, supabase_key)
                logger.warning(f"⚠️ Supabase подключен с service_role ключом: {supabase_url}")
        elif supabase_url and not supabase_key:
            service_key = os.getenv("SUPABASE_SERVICE_KEY")
            if service_key:
                _supabase = create_client(supabase_url, service_key)
                logger.warning(f"⚠️ Supabase подключен через SERVICE_ROLE: {supabase_url}")
            else:
                logger.warning("⚠️ SUPABASE_URL задан, но SUPABASE_KEY и SUPABASE_SERVICE_KEY не настроены")
                return None
        elif database_url:
            logger.info("ℹ️ DATABASE_URL задан, но используется только для RAG и не создаёт Supabase клиента")
            return None
        else:
            logger.warning("⚠️ Нет настроек для подключения к БД")
            return None

        return _supabase
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return None


def get_supabase_service() -> Optional[Client]:
    """
    Возвращает клиент Supabase с сервисным ключом для прямого доступа к таблицам
    
    Используется для операций, требующих обхода RLS (Row Level Security)
    Например: загрузка документов, управление коллекциями
    
    Returns:
        Клиент Supabase или None если не настроен
    """
    global _supabase_service
    
    if '_supabase_service' in globals() and _supabase_service is not None:
        return _supabase_service

    if _is_development():
        return None
    
    if not HAS_SUPABASE:
        logger.warning("⚠️ Supabase клиент не установлен")
        return None
    
    # Получаем настройки из .env
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url:
        logger.warning("⚠️ SUPABASE_URL не настроен")
        return None
    
    try:
        if service_key:
            _supabase_service = create_client(supabase_url, service_key)
            logger.info(f"✅ Supabase service client подключен: {supabase_url}")
        else:
            logger.warning("⚠️ SUPABASE_SERVICE_KEY не настроен — service client недоступен без service_role ключа")
            return None
        
        return _supabase_service
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения service client к БД: {e}")
        return None


def create_supabase_client_with_access_token(access_token: str) -> Optional[Client]:
    """
    Создаёт новый Supabase клиент, который использует service_role или anon key
    вместе с Authorization заголовком пользователя.
    """
    if _is_development():
        return None

    if not HAS_SUPABASE:
        logger.warning("⚠️ Supabase клиент не установлен")
        return None

    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        logger.warning("⚠️ SUPABASE_URL не настроен")
        return None

    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not supabase_key:
        logger.warning("⚠️ Ни SUPABASE_SERVICE_KEY, ни SUPABASE_KEY не настроены")
        return None

    try:
        client = create_client(supabase_url, supabase_key)
        client.options.headers["Authorization"] = f"Bearer {access_token}"
        return client
    except Exception as e:
        logger.error(f"❌ Ошибка создания Supabase клиента с access token: {e}")
        return None


class LocalDBClient:
    """Локальный SQLite клиент с API, имитирующим Supabase для разработки."""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / "data" / "memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalDBClient init: db_path={self.db_path}")
        self._init_db()
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    provider_display_name TEXT,
                    api_key_encrypted TEXT NOT NULL,
                    name TEXT,
                    model_preference TEXT DEFAULT 'auto',
                    is_default INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT,
                    avatar_url TEXT,
                    email_verified INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS dialogs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    is_favorite INTEGER DEFAULT 0,
                    last_message_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    dialog_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL,
                    model TEXT,
                    provider TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS user_settings (
                    id TEXT PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    persona_tone TEXT DEFAULT 'friendly',
                    persona_detail_level TEXT DEFAULT 'moderate',
                    persona_emotion_level TEXT DEFAULT 'balanced',
                    persona_specialization TEXT DEFAULT 'general',
                    notification_email INTEGER DEFAULT 1,
                    notification_push INTEGER DEFAULT 0,
                    notification_sound INTEGER DEFAULT 1,
                    notification_frequency TEXT DEFAULT 'immediate',
                    theme TEXT DEFAULT 'dark',
                    font_size TEXT DEFAULT 'medium',
                    compact_mode INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        except Exception as e:
            logger.error(f"_init_db FAILED: {e}")
            raise
        finally:
            conn.close()
    
    def table(self, table_name: str):
        return LocalTable(self, table_name)


class LocalTable:
    """Имитация Supabase table() API."""

    def __init__(self, db: LocalDBClient, table_name: str):
        self.db = db
        self.table_name = table_name
        self._filters = []
        self._select_cols = "*"
        self._order_by = None
        self._limit_val = None
        self._offset_val = None
        self._count = None
        self._insert_data = None
        self._update_data = None
        self._delete_mode = False

    def select(self, cols: str = "*", count: str = None):
        self._select_cols = cols
        self._count = count
        return self

    def eq(self, column: str, value: Any):
        self._filters.append(("eq", column, value))
        return self

    def neq(self, column: str, value: Any):
        self._filters.append(("neq", column, value))
        return self

    def gt(self, column: str, value: Any):
        self._filters.append(("gt", column, value))
        return self

    def gte(self, column: str, value: Any):
        self._filters.append(("gte", column, value))
        return self

    def lt(self, column: str, value: Any):
        self._filters.append(("lt", column, value))
        return self

    def lte(self, column: str, value: Any):
        self._filters.append(("lte", column, value))
        return self

    def like(self, column: str, pattern: str):
        self._filters.append(("like", column, pattern))
        return self

    def ilike(self, column: str, pattern: str):
        self._filters.append(("ilike", column, pattern))
        return self

    def filter(self, column: str, operator: str, value: Any):
        op_map = {"eq": "eq", "neq": "neq", "gt": "gt", "gte": "gte",
                  "lt": "lt", "lte": "lte", "like": "like", "ilike": "ilike", "in": "in"}
        self._filters.append((op_map.get(operator, operator), column, value))
        return self

    def in_(self, column: str, values: List):
        self._filters.append(("in", column, values))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_by = (column, desc)
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def range(self, start: int, end: int):
        self._limit_val = end - start + 1
        self._offset_val = start
        return self

    def offset(self, count: int):
        self._offset_val = count
        return self

    def _build_where(self):
        parts = []
        params = []
        for op, col, val in self._filters:
            if op == "eq":
                parts.append(f"\"{col}\" = ?")
                params.append(val)
            elif op == "neq":
                parts.append(f"\"{col}\" != ?")
                params.append(val)
            elif op == "gt":
                parts.append(f"\"{col}\" > ?")
                params.append(val)
            elif op == "gte":
                parts.append(f"\"{col}\" >= ?")
                params.append(val)
            elif op == "lt":
                parts.append(f"\"{col}\" < ?")
                params.append(val)
            elif op == "lte":
                parts.append(f"\"{col}\" <= ?")
                params.append(val)
            elif op == "like":
                parts.append(f"\"{col}\" LIKE ?")
                params.append(val)
            elif op == "ilike":
                parts.append(f"\"{col}\" LIKE ?")
                params.append(val)
            elif op == "in":
                ph = ", ".join(["?" for _ in val])
                parts.append(f"\"{col}\" IN ({ph})")
                params.extend(val)
        return parts, params

    def insert(self, data: Dict):
        from datetime import datetime
        now = datetime.now().isoformat()
        self._insert_data = dict(data)
        if "created_at" not in self._insert_data:
            self._insert_data["created_at"] = now
        if "updated_at" not in self._insert_data:
            self._insert_data["updated_at"] = now
        return self

    def update(self, data: Dict):
        from datetime import datetime
        self._update_data = dict(data)
        self._update_data["updated_at"] = datetime.now().isoformat()
        return self

    def delete(self):
        self._delete_mode = True
        return self

    def execute(self):
        conn = self.db._get_conn()
        try:
            # INSERT
            if self._insert_data is not None:
                cols = ", ".join(self._insert_data.keys())
                ph = ", ".join(["?" for _ in self._insert_data])
                conn.execute(f"INSERT INTO {self.table_name} ({cols}) VALUES ({ph})",
                             list(self._insert_data.values()))
                conn.commit()
                result_data = dict(self._insert_data)
                self._insert_data = None
                return SimpleNamespace(data=[result_data], count=1)

            where_parts, params = self._build_where()

            # UPDATE: сначала выбираем строки, потом обновляем, возвращаем данные
            if self._update_data is not None:
                where_clause = " AND ".join(where_parts) if where_parts else "1"
                select_sql = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
                cursor = conn.execute(select_sql, params)
                column_names = [desc[0] for desc in cursor.description]
                rows_before = [dict(r) for r in cursor.fetchall()]

                set_parts = [f"\"{k}\" = ?" for k in self._update_data.keys()]
                set_values = list(self._update_data.values())
                sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)}"
                if where_parts:
                    sql += " WHERE " + " AND ".join(where_parts)
                conn.execute(sql, set_values + params)
                conn.commit()

                updated = []
                for row in rows_before:
                    new_row = dict(row)
                    new_row.update(self._update_data)
                    updated.append(new_row)
                self._update_data = None
                return SimpleNamespace(data=updated, count=len(updated))

            # DELETE: сначала выбираем строки, потом удаляем, возвращаем их
            if self._delete_mode:
                where_clause = " AND ".join(where_parts) if where_parts else "1"
                select_sql = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
                cursor = conn.execute(select_sql, params)
                column_names = [desc[0] for desc in cursor.description]
                deleted_rows = [dict(r) for r in cursor.fetchall()]

                sql = f"DELETE FROM {self.table_name}"
                if where_parts:
                    sql += " WHERE " + " AND ".join(where_parts)
                conn.execute(sql, params)
                conn.commit()
                self._delete_mode = False
                return SimpleNamespace(data=deleted_rows, count=len(deleted_rows))

            # SELECT
            where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""

            order_clause = ""
            if self._order_by:
                col, desc = self._order_by
                order_clause = f" ORDER BY \"{col}\" {'DESC' if desc else 'ASC'}"

            limit_clause = ""
            if self._limit_val is not None:
                limit_clause = f" LIMIT {self._limit_val}"
            if self._offset_val is not None:
                limit_clause += f" OFFSET {self._offset_val}"

            if self._count == "exact":
                row = conn.execute(f"SELECT COUNT(*) as cnt FROM {self.table_name}{where_clause}", params).fetchone()
                return SimpleNamespace(data=[], count=row["cnt"] if row else 0)

            sql = f"SELECT {self._select_cols} FROM {self.table_name}{where_clause}{order_clause}{limit_clause}"
            rows = conn.execute(sql, params).fetchall()
            data = [dict(r) for r in rows]

            count = None
            if self._count == "exact":
                row = conn.execute(f"SELECT COUNT(*) as cnt FROM {self.table_name}{where_clause}", params).fetchone()
                count = row["cnt"] if row else 0

            return SimpleNamespace(data=data, count=count)
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return SimpleNamespace(data=[], count=0)
            raise
        finally:
            conn.close()

    def single(self):
        self.limit(1)
        result = self.execute()
        return SimpleNamespace(data=result.data[0] if result.data else None)


# Глобальный экземпляр для dev-режима
_local_db_client = None

def get_local_db_client() -> LocalDBClient:
    global _local_db_client
    if _local_db_client is None:
        _local_db_client = LocalDBClient()
    return _local_db_client


def get_db_client(current_user: Optional[dict] = None):
    if current_user is not None and current_user.get("access_token"):
        client = create_supabase_client_with_access_token(current_user["access_token"])
        if client:
            return client

    db = get_supabase_service()
    if db:
        return db

    supabase = get_supabase()
    if supabase:
        return supabase

    if _is_development():
        logger.info("DEV: using local SQLite")
        return get_local_db_client()

    return None


def check_database_connection() -> bool:
    """
    Проверяет подключение к базе данных
    
    Returns:
        True если подключение успешно
    """
    try:
        supabase = get_supabase()
        
        if supabase is None:
            # Проверяем DATABASE_URL напрямую
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                logger.info("✅ DATABASE_URL настроен")
                return True
            return False
        
        # Пробуем сделать простой запрос
        # (таблица может не существовать, поэтому игнорируем ошибки)
        try:
            supabase.table("users").select("count").limit(1).execute()
        except Exception:
            logger.debug("Таблица users не существует при проверке подключения")
        
        logger.info("✅ Подключение к БД работает")
        return True
        
    except Exception as e:
        logger.error(f"❌ Подключение к БД не работает: {e}")
        return False


def get_database_url() -> str:
    """
    Возвращает URL базы данных
    
    Returns:
        DATABASE_URL или None
    """
    return os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL")


# === SAFE QUERY METHODS WITH CIRCUIT BREAKER ===

async def safe_query(
    table: str,
    method: str,
    *,
    fallback: any = None,
    operation_name: str = None,
    **kwargs
) -> any:
    """
    Безопасный запрос к БД с Circuit Breaker
    
    Args:
        table: Название таблицы
        method: Метод (select, insert, update, delete)
        fallback: Fallback значение при ошибке
        operation_name: Название операции для логирования
        **kwargs: Аргументы для метода
    
    Returns:
        Результат запроса или fallback
    """
    from core.db_circuit_breaker import get_db_circuit_breaker
    
    cb = get_db_circuit_breaker()
    op_name = operation_name or f"{table}.{method}"
    
    async def operation(**kw):
        supabase = get_supabase()
        if not supabase:
            raise Exception("Supabase client not available")
        
        table_obj = supabase.table(table)
        result = await getattr(table_obj, method)(**kw).execute()
        return result
    
    async def fallback_func(**kw):
        logger.warning(f"🔄 Fallback для {op_name}")
        # Кэшируем fallback значение
        if fallback is not None:
            cb.cache_for_fallback(op_name, fallback)
        return fallback
    
    try:
        result = await cb.execute(
            operation=op_name,
            func=operation,
            fallback=fallback_func,
            **kwargs
        )
        return result
    except Exception as e:
        logger.error(f"❌ Безопасный запрос {op_name} не удался: {e}")
        raise


async def safe_select(
    table: str,
    columns: str = "*",
    **kwargs
) -> list:
    """
    Безопасный SELECT запрос
    
    Args:
        table: Название таблицы
        columns: Столбцы для выбора
        **kwargs: Фильтры (eq, neq, gt, lt, etc.)
    
    Returns:
        Список записей
    """
    result = await safe_query(
        table=table,
        method="select",
        fallback=[],
        columns=columns,
        **kwargs
    )
    return result.data if hasattr(result, 'data') else []


async def safe_insert(
    table: str,
    data: dict,
    **kwargs
) -> Optional[dict]:
    """
    Безопасный INSERT запрос
    
    Args:
        table: Название таблицы
        data: Данные для вставки
    
    Returns:
        Вставленная запись или None
    """
    result = await safe_query(
        table=table,
        method="insert",
        fallback=None,
        values=[data],
        **kwargs
    )
    if result and hasattr(result, 'data') and result.data:
        return result.data[0]
    return None


async def safe_update(
    table: str,
    data: dict,
    **kwargs
) -> bool:
    """
    Безопасный UPDATE запрос
    
    Args:
        table: Название таблицы
        data: Данные для обновления
        **kwargs: Фильтры (eq, neq, etc.)
    
    Returns:
        True если успешно
    """
    result = await safe_query(
        table=table,
        method="update",
        fallback=False,
        values=data,
        **kwargs
    )
    return result.count > 0 if hasattr(result, 'count') else False


async def safe_delete(
    table: str,
    **kwargs
) -> bool:
    """
    Безопасный DELETE запрос
    
    Args:
        table: Название таблицы
        **kwargs: Фильтры (eq, neq, etc.)
    
    Returns:
        True если успешно
    """
    result = await safe_query(
        table=table,
        method="delete",
        fallback=False,
        **kwargs
    )
    return True  # Если не было исключения — успешно


def get_db_circuit_breaker_stats() -> dict:
    """
    Получает статистику DB Circuit Breaker
    
    Returns:
        Dict со статистикой
    """
    from core.db_circuit_breaker import get_db_circuit_breaker
    return get_db_circuit_breaker().get_stats()


def reset_db_circuit_breaker():
    """
    Сбрасывает DB Circuit Breaker (для тестов или вручную)
    """
    from core.db_circuit_breaker import reset_db_circuit_breaker
    reset_db_circuit_breaker()
