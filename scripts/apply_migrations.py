import os
import sys

os.chdir(r'C:\пад ал датабаз а  чистый\PAD+ AI чистый')

# Read DATABASE_URL from .env
with open('.env', encoding='utf-8') as f:
    env_lines = f.readlines()

db_url = None
for line in env_lines:
    if line.startswith('DATABASE_URL='):
        db_url = line.strip().split('=', 1)[1]
        break

if not db_url:
    print('DATABASE_URL not found in .env')
    sys.exit(1)

# Remove quotes if present
db_url = db_url.strip("'").strip('"')

print(f'Connecting to Supabase PostgreSQL...')

import psycopg2
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

# Migration 020 - experiences
print('--- Applying 020_experiences_postgres.sql ---')
cur.execute("""
    CREATE TABLE IF NOT EXISTS experiences (
        id BIGSERIAL PRIMARY KEY,
        dialog_id TEXT NOT NULL,
        user_message TEXT NOT NULL,
        ai_response TEXT,
        interaction_type TEXT NOT NULL,
        signals JSONB DEFAULT '{}',
        significance REAL DEFAULT 0.0,
        expectation TEXT DEFAULT '',
        reality TEXT DEFAULT '',
        delta TEXT DEFAULT '',
        lessons JSONB DEFAULT '[]',
        strategy_success REAL DEFAULT 0.0,
        impulse_before JSONB DEFAULT '{}',
        emotion_before JSONB DEFAULT '{}',
        persona_before JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
""")
print('  - Table experiences created/verified')

cur.execute("CREATE INDEX IF NOT EXISTS idx_experiences_dialog_id ON experiences(dialog_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_experiences_interaction_type ON experiences(interaction_type)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_experiences_significance ON experiences(significance DESC)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_experiences_created_at ON experiences(created_at DESC)")
print('  - Indexes created')

cur.execute("ALTER TABLE experiences ENABLE ROW LEVEL SECURITY")
cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname='Service role full access experiences') THEN
            CREATE POLICY "Service role full access experiences" ON experiences TO service_role USING (true) WITH CHECK (true);
        END IF;
    END
    $$
""")
cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname='Anon read experiences') THEN
            CREATE POLICY "Anon read experiences" ON experiences FOR SELECT TO anon USING (true);
        END IF;
    END
    $$
""")
print('  - RLS policies created')

# Migration 021 - user_personas
print('--- Applying 021_user_personas_postgres.sql ---')
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_personas (
        user_id TEXT PRIMARY KEY,
        data JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
""")
print('  - Table user_personas created/verified')

cur.execute("CREATE INDEX IF NOT EXISTS idx_user_personas_updated ON user_personas(updated_at DESC)")
print('  - Index created')

cur.execute("ALTER TABLE user_personas ENABLE ROW LEVEL SECURITY")
cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname='Service role full access user_personas') THEN
            CREATE POLICY "Service role full access user_personas" ON user_personas TO service_role USING (true) WITH CHECK (true);
        END IF;
    END
    $$
""")
cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname='Anon read user_personas') THEN
            CREATE POLICY "Anon read user_personas" ON user_personas FOR SELECT TO anon USING (true);
        END IF;
    END
    $$
""")
print('  - RLS policies created')

cur.close()
conn.close()
print()
print('Both migrations applied successfully!')
