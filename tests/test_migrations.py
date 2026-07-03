"""Тесты миграций БД"""

import pytest


EXPECTED_TABLES = {
    "users",
    "user_api_keys",
    "chat_sessions",
    "chat_messages",
    "provider_configs",
    "user_settings",
    "dialogs",
    "messages",
    "documents",
    "document_collections",
    "document_chunks",
    "xray_traces",
    "persona_state",
    "roots_knowledge",
    "emotion_state",
    "episodes",
    "episode_relations",
    "semantic_knowledge",
    "procedure_applications",
    "experiences",
    "user_personas",
}


class TestMigrations:
    def test_migration_file_exists(self):
        from pathlib import Path
        migration_path = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "0001_initial_schema.py"
        assert migration_path.exists(), "Migration file 0001_initial_schema.py not found"

    def test_alembic_config_exists(self):
        from pathlib import Path
        alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
        assert alembic_ini.exists(), "alembic.ini not found"

    def test_alembic_env_exists(self):
        from pathlib import Path
        env_py = Path(__file__).resolve().parent.parent / "alembic" / "env.py"
        assert env_py.exists(), "alembic/env.py not found"

    def test_migrate_script_exists(self):
        from pathlib import Path
        migrate_py = Path(__file__).resolve().parent.parent / "scripts" / "migrate.py"
        assert migrate_py.exists(), "scripts/migrate.py not found"

    def test_migration_has_downgrade(self):
        import importlib.util
        from pathlib import Path

        migration_path = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "0001_initial_schema.py"
        spec = importlib.util.spec_from_file_location("migration", migration_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        assert hasattr(mod, "downgrade"), "Migration must have downgrade function"
        assert mod.downgrade.__code__.co_code != b'\x97\x00', "downgrade must not be empty"

    def test_information_schema_table_list(self):
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        from alembic import command
        from alembic.config import Config
        from pathlib import Path
        import os

        project_root = Path(__file__).resolve().parent.parent
        alembic_cfg = Config(str(project_root / "alembic.ini"))

        db_url = os.getenv("DATABASE_URL")
        if db_url and "localhost" not in db_url and "supabase" in db_url:
            from sqlalchemy import create_engine, text
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text(query))
                existing = {row[0] for row in result}

            missing = EXPECTED_TABLES - existing
            assert not missing, f"Missing tables: {missing}"
        else:
            pytest.skip("No live DATABASE_URL configured for table check")

    def test_initial_migration_combines_all_sql_files(self):
        from pathlib import Path
        sql_dir = Path(__file__).resolve().parent.parent / "backend" / "database" / "migrations"
        sql_files = sorted(f.name for f in sql_dir.glob("*.sql"))

        assert len(sql_files) == 16, f"Expected 16 SQL files, found {len(sql_files)}"
        expected_prefixes = [f"{i:03d}" for i in range(1, 23)] + ["017"]
        for sf in sql_files:
            assert any(sf.startswith(p) for p in expected_prefixes), f"Unexpected SQL file: {sf}"
