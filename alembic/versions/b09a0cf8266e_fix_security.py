"""fix_security — RLS для alembic_version + SECURITY INVOKER для views

Revision ID: b09a0cf8266e
Revises: 0001_initial_schema
Create Date: 2026-07-03 23:26:15.850591
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b09a0cf8266e'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. RLS для alembic_version (системная таблица миграций)
    op.execute("ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE policyname = 'service_role_only' AND tablename = 'alembic_version'
            ) THEN
                CREATE POLICY "service_role_only" ON alembic_version
                    FOR ALL TO service_role USING (true) WITH CHECK (true);
            END IF;
        END $$;
    """)

    # 2. user_stats — SECURITY INVOKER (чтобы RLS срабатывал для вызывающего)
    op.execute("""
        ALTER VIEW user_stats SET (security_invoker = true);
    """)

    # 3. dialog_stats — SECURITY INVOKER
    op.execute("""
        ALTER VIEW dialog_stats SET (security_invoker = true);
    """)


def downgrade() -> None:
    # Откат: убрать политику с alembic_version
    op.execute("""
        DROP POLICY IF EXISTS "service_role_only" ON alembic_version;
        ALTER TABLE alembic_version DISABLE ROW LEVEL SECURITY;
    """)

    # Откат views к SECURITY DEFINER (дефолт)
    op.execute("ALTER VIEW user_stats SET (security_invoker = false);")
    op.execute("ALTER VIEW dialog_stats SET (security_invoker = false);")