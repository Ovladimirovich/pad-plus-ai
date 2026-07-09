"""
Миграция данных Knowledge Graph из SQLite в Supabase.

Запуск:
    cd backend && python ../scripts/migrate_to_supabase.py

Что делает:
  1. Подключается к SQLite (data/knowledge.db)
  2. Подключается к Supabase
  3. Создаёт таблицы knowledge_concepts и knowledge_relations (если нет)
  4. Переносит все концепции и связи
  5. Пропускает дубликаты (по name)

Требует:
  - SUPABASE_URL и SUPABASE_KEY в .env
  - или DATABASE_URL для прямого pg-подключения
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Загружаем .env (если есть)
from pathlib import Path
env_path = Path(os.path.dirname(__file__)).parent / '.env'
if env_path.exists():
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
    print(f"Загружен .env: {env_path}")
else:
    print(".env не найден, использую переменные окружения")

import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("migrate")

# Supabase
from core.supabase_client import get_supabase_service, get_supabase
client = get_supabase_service() or get_supabase()
if client is None:
    log.error("Supabase не подключён. Проверь SUPABASE_URL и SUPABASE_KEY в .env")
    sys.exit(1)

# Прямое pg-подключение для создания таблиц
database_url = os.getenv("DATABASE_URL")
if database_url:
    import psycopg2
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_concepts (
            id TEXT PRIMARY KEY, name TEXT NOT NULL,
            type TEXT DEFAULT 'concept', confidence REAL DEFAULT 0.5,
            source TEXT DEFAULT 'user', created_at TIMESTAMPTZ DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_relations (
            id BIGSERIAL PRIMARY KEY,
            source_id TEXT NOT NULL REFERENCES knowledge_concepts(id) ON DELETE CASCADE,
            target_id TEXT NOT NULL REFERENCES knowledge_concepts(id) ON DELETE CASCADE,
            type TEXT DEFAULT 'related', weight REAL DEFAULT 1.0,
            confidence REAL DEFAULT 0.5, created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_concepts_name ON knowledge_concepts USING gin (to_tsvector('simple', name))")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_relations_source ON knowledge_relations(source_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_relations_target ON knowledge_relations(target_id)")
    conn.commit()
    cur.close()
    conn.close()
    log.info("Таблицы созданы/проверены через pg")

# SQLite
sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge.db")
if not os.path.exists(sqlite_path):
    log.warning(f"SQLite БД не найдена: {sqlite_path}")
    sys.exit(0)

import sqlite3
sq = sqlite3.connect(sqlite_path)
sq.row_factory = sqlite3.Row

# Перенос концепций
cur = sq.cursor()
cur.execute("SELECT * FROM concepts")
rows = cur.fetchall()
log.info(f"Найдено {len(rows)} концепций в SQLite")

existing = set()
try:
    resp = client.table("knowledge_concepts").select("name").execute()
    for r in (resp.data or []):
        existing.add(r["name"].lower())
except Exception:
    pass

migrated_c = 0
for row in rows:
    name_lower = row["name"].lower()
    if name_lower in existing:
        log.info(f"  Пропуск (уже есть): {row['name']}")
        continue
    try:
        client.table("knowledge_concepts").insert({
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "confidence": row["confidence"],
            "source": row["source"],
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata"]),
        }).execute()
        existing.add(name_lower)
        migrated_c += 1
        log.info(f"  + {row['name']} ({row['type']})")
    except Exception as e:
        log.error(f"  Ошибка {row['name']}: {e}")

# Перенос связей
cur.execute("SELECT * FROM relations")
rows = cur.fetchall()
log.info(f"Найдено {len(rows)} связей в SQLite")

# Получаем ID концепций из Supabase
concept_ids = set()
try:
    resp = client.table("knowledge_concepts").select("id").execute()
    for r in (resp.data or []):
        concept_ids.add(r["id"])
except Exception:
    pass

migrated_r = 0
for row in rows:
    if row["source_id"] not in concept_ids or row["target_id"] not in concept_ids:
        log.warning(f"  Пропуск связи: концепция не найдена в Supabase")
        continue
    try:
        client.table("knowledge_relations").insert({
            "source_id": row["source_id"],
            "target_id": row["target_id"],
            "type": row["type"],
            "weight": row["weight"],
            "confidence": row["confidence"],
            "created_at": row["created_at"],
        }).execute()
        migrated_r += 1
    except Exception as e:
        log.error(f"  Ошибка связи: {e}")

sq.close()
log.info(f"Готово: перенесено {migrated_c} концепций, {migrated_r} связей")
