-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create RAG embeddings table
CREATE TABLE IF NOT EXISTS rag_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    embedding vector(384),
    user_id UUID,
    collection_name TEXT DEFAULT 'default',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 3: Create index for vector search
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_embedding 
ON rag_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Step 4: Create memory facts table
CREATE TABLE IF NOT EXISTS memory_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fact TEXT NOT NULL,
    embedding vector(384),
    user_id UUID,
    category TEXT,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 5: Create index for memory facts
CREATE INDEX IF NOT EXISTS idx_memory_facts_embedding 
ON memory_facts USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Step 6: Enable Row Level Security
ALTER TABLE rag_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_facts ENABLE ROW LEVEL SECURITY;

-- Step 7: Create search function
CREATE OR REPLACE FUNCTION search_rag_embeddings(
    query_embedding vector(384),
    match_count int DEFAULT 5,
    filter_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    text TEXT,
    user_id UUID,
    collection_name TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
#variable_conflict use_column
BEGIN
    RETURN QUERY
    SELECT
        id,
        text,
        user_id,
        collection_name,
        metadata,
        1 - (embedding <=> query_embedding) AS similarity
    FROM rag_embeddings
    WHERE filter_user_id IS NULL OR user_id = filter_user_id
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Step 8: Verify setup
SELECT '✅ pgvector enabled' as status;
SELECT COUNT(*) as table_count FROM pg_tables WHERE tablename IN ('rag_embeddings', 'memory_facts');
SELECT COUNT(*) as index_count FROM pg_indexes WHERE tablename IN ('rag_embeddings', 'memory_facts');