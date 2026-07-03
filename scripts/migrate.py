"""
Скрипт для запуска Alembic миграций при старте приложения.

Использование:
    python -m scripts.migrate          # Применить миграции
    python -m scripts.migrate --check  # Только проверить статус
    python -m scripts.migrate --sql    # Вывести SQL без применения
"""

import os
import sys
import argparse
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_migrations(dry_run: bool = False, check: bool = False) -> bool:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(str(Path(project_root) / "alembic.ini"))
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL не задан в окружении")
        return False

    if check:
        command.check(alembic_cfg)
        print("Миграции в порядке")
        return True

    if dry_run:
        command.upgrade(alembic_cfg, revision="head", sql=True)
    else:
        command.upgrade(alembic_cfg, revision="head")

    return True


def migrate_at_startup() -> bool:
    try:
        print("Запуск Alembic миграций...")
        alembic_cfg_path = str(Path(project_root) / "alembic.ini")
        os.environ["ALEMBIC_CONFIG"] = alembic_cfg_path
        return run_migrations()
    except Exception as e:
        print(f"Ошибка при запуске миграций: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление миграциями БД")
    parser.add_argument("--check", action="store_true", help="Проверить статус миграций")
    parser.add_argument("--sql", action="store_true", help="Вывести SQL без применения")
    args = parser.parse_args()

    success = run_migrations(dry_run=args.sql, check=args.check)
    sys.exit(0 if success else 1)
