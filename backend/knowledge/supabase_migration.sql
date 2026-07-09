-- Knowledge Graph: создание таблиц в Supabase
-- Запустите этот SQL в SQL Editor Supabase (https://supabase.com/dashboard)

-- Таблица концепций
CREATE TABLE IF NOT EXISTS knowledge_concepts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'concept',
    confidence REAL DEFAULT 0.5,
    source TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Индекс для поиска по имени (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_knowledge_concepts_name ON knowledge_concepts USING gin (to_tsvector('simple', name));

-- Таблица связей
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES knowledge_concepts(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES knowledge_concepts(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'related',
    weight REAL DEFAULT 1.0,
    confidence REAL DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для связей
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_source ON knowledge_relations(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_target ON knowledge_relations(target_id);

-- Разрешаем RLS (Row Level Security) — отключаем для сервисного ключа
ALTER TABLE knowledge_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_relations ENABLE ROW LEVEL SECURITY;

-- Политики: сервисный ключ имеет полный доступ
CREATE POLICY "Service key full access" ON knowledge_concepts
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service key full access" ON knowledge_relations
    FOR ALL USING (true) WITH CHECK (true);
