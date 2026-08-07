"""
Фаза 3: Миграция Episodic Memory для поддержки user_id.

Добавляет колонку user_id в таблицу episodes (и индекс по ней),
если она отсутствует. Совместима со старой схемой SQLite.

Запуск:
    python scripts/migrate_episodic_user_id.py [путь_до_episodic.db]
"""

import os
import sqlite3
import sys


def _default_db_path() -> str:
    """Путь по умолчанию к БД эпизодов (data/episodic.db относительно backend)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", "episodic.db")


def migrate_episodic(db_path: str = None) -> bool:
    """Добавляет колонку user_id и индекс, если их ещё нет."""
    if db_path is None:
        db_path = _default_db_path()

    if not os.path.exists(db_path):
        print(f"БД эпизодов не найдена ({db_path}), таблица не существует. Пропуск.")
        return False

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(episodes)")
        columns = [row[1] for row in cursor.fetchall()]

        if "user_id" not in columns:
            print("Миграция: добавление колонки user_id в episodes...")
            cursor.execute("ALTER TABLE episodes ADD COLUMN user_id TEXT")
            conn.commit()
            migrated = True
        else:
            migrated = False

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episodes_user_id ON episodes(user_id)"
        )
        conn.commit()
        return migrated
    finally:
        conn.close()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    changed = migrate_episodic(arg)
    if changed:
        print("✅ Миграция выполнена: колонка user_id добавлена.")
    else:
        print("ℹ️ Миграция не требуется: user_id уже существует.")