-- 021_user_personas_postgres.sql
-- PostgreSQL таблица для UserPersona
-- Замена JSON-файла на персистентное хранение в БД

CREATE TABLE IF NOT EXISTS user_personas (
    user_id TEXT PRIMARY KEY,
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_personas_updated ON user_personas(updated_at DESC);

ALTER TABLE user_personas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access user_personas" ON user_personas TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Anon read user_personas" ON user_personas FOR SELECT TO anon USING (true);
