-- ============================================================================
-- PAD+ AI v4.0 — Document Chunks with pgvector
-- ============================================================================

-- Убедимся что расширение vector установлено
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- DOCUMENT CHUNKS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для быстрого поиска по document_id
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);

-- Индекс для векторного поиска (IVFFlat с 100 центроидами — оптимально для <1M векторов)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks
    USING ivf (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Индекс для полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_gin ON document_chunks
    USING gin (to_tsvector('russian', content));

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Через document_id получаем user_id из таблицы documents
CREATE POLICY "Users can view own document chunks"
    ON document_chunks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_chunks.document_id
            AND documents.user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert own document chunks"
    ON document_chunks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_chunks.document_id
            AND documents.user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can delete own document chunks"
    ON document_chunks FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_chunks.document_id
            AND documents.user_id::text = auth.uid()::text
        )
    );

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
