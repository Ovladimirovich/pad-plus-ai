"""add_analytics_events — таблица аналитических событий

Revision ID: dd82c3a8ee17
Revises: b09a0cf8266e
Create Date: 2026-07-04 00:18:43.047933
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'dd82c3a8ee17'
down_revision: Union[str, None] = 'b09a0cf8266e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Таблица аналитических событий
    op.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id BIGSERIAL PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
            event TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_event ON analytics_events(event);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at DESC);")

    # RLS
    op.execute("ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE policyname = 'Users can view own analytics events' 
                AND tablename = 'analytics_events'
            ) THEN
                CREATE POLICY "Users can view own analytics events" ON analytics_events
                    FOR SELECT USING (user_id = auth.uid());
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE policyname = 'Service role full access analytics events' 
                AND tablename = 'analytics_events'
            ) THEN
                CREATE POLICY "Service role full access analytics events" ON analytics_events
                    TO service_role USING (true) WITH CHECK (true);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS \"Service role full access analytics events\" ON analytics_events;")
    op.execute("DROP POLICY IF EXISTS \"Users can view own analytics events\" ON analytics_events;")
    op.execute("ALTER TABLE analytics_events DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP TABLE IF EXISTS analytics_events;")