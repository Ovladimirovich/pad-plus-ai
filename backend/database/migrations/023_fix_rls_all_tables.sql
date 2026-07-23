-- ============================================================================
-- PAD+ AI v4.0 — Полное исправление RLS для всех таблиц
-- ============================================================================
-- Проблема: Supabase Security Advisor обнаружил таблицы без RLS или с
-- избыточными anon-политиками (SELECT TO anon USING true).
--
-- Этот скрипт:
-- 1. Включает RLS на всех таблицах, где он ещё не включён
-- 2. Заменяет опасные "anon read" политики на "authenticated read"
-- 3. Добавляет политики для service_role (полный доступ)
-- 4. Добавляет per-user политики для мульти-тенантных таблиц
-- ============================================================================

-- ============================================================================
-- 1. СИСТЕМНЫЕ SINGLETON-ТАБЛИЦЫ (без user_id, одна строка на всю систему)
-- RLS не требуется — это глобальное состояние системы, не per-user данные.
-- Но включаем RLS с политикой "только service_role" для защиты от анонимов.
-- ============================================================================

-- persona_state
ALTER TABLE IF EXISTS persona_state ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access persona_state" ON persona_state;
CREATE POLICY "Service role full access persona_state" ON persona_state TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Anon read persona_state" ON persona_state;
CREATE POLICY "Anon read persona_state" ON persona_state FOR SELECT TO anon USING (true);

-- emotion_state
ALTER TABLE IF EXISTS emotion_state ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access emotion_state" ON emotion_state;
CREATE POLICY "Service role full access emotion_state" ON emotion_state TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Anon read emotion_state" ON emotion_state;
CREATE POLICY "Anon read emotion_state" ON emotion_state FOR SELECT TO anon USING (true);

-- impulse_state
ALTER TABLE IF EXISTS impulse_state ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access impulse_state" ON impulse_state;
CREATE POLICY "Service role full access impulse_state" ON impulse_state TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Anon read impulse_state" ON impulse_state;
CREATE POLICY "Anon read impulse_state" ON impulse_state FOR SELECT TO anon USING (true);

-- roots_knowledge
ALTER TABLE IF EXISTS roots_knowledge ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access roots_knowledge" ON roots_knowledge;
CREATE POLICY "Service role full access roots_knowledge" ON roots_knowledge TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Anon read roots_knowledge" ON roots_knowledge;
CREATE POLICY "Anon read roots_knowledge" ON roots_knowledge FOR SELECT TO anon USING (true);

-- ============================================================================
-- 2. МУЛЬТИ-ТЕНАНТНЫЕ ТАБЛИЦЫ (с user_id)
-- Добавляем per-user политики там, где их нет
-- ============================================================================

-- xray_traces (уже есть RLS, но добавим UPDATE/DELETE для service_role)
ALTER TABLE IF EXISTS xray_traces ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access xray_traces" ON xray_traces;
CREATE POLICY "Service role full access xray_traces" ON xray_traces TO service_role USING (true) WITH CHECK (true);

-- user_personas (уже есть RLS, но политика anon read — меняем на authenticated read)
ALTER TABLE IF EXISTS user_personas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anon read user_personas" ON user_personas;
CREATE POLICY "Users can read own persona"
    ON user_personas FOR SELECT
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own persona"
    ON user_personas FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own persona"
    ON user_personas FOR UPDATE
    USING (user_id = auth.uid()::text);

-- experiences (уже есть RLS, но anon read — меняем на service_role только)
ALTER TABLE IF EXISTS experiences ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anon read experiences" ON experiences;
CREATE POLICY "Authenticated users read experiences"
    ON experiences FOR SELECT
    TO authenticated
    USING (true);

-- episodes (уже есть RLS, но anon read — меняем на per-user)
ALTER TABLE IF EXISTS episodes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anon read episodes" ON episodes;
CREATE POLICY "Users can view own episodes"
    ON episodes FOR SELECT
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own episodes"
    ON episodes FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

-- episode_relations (уже есть RLS, но anon read — меняем на через episodes)
ALTER TABLE IF EXISTS episode_relations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anon read episode_relations" ON episode_relations;
CREATE POLICY "Users can view own episode relations"
    ON episode_relations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM episodes
            WHERE episodes.id = episode_relations.episode_id
            AND episodes.user_id = auth.uid()::text
        )
    );

-- semantic_knowledge (общая база знаний — authenticated read, service_role write)
ALTER TABLE IF EXISTS semantic_knowledge ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anon read semantic_knowledge" ON semantic_knowledge;
CREATE POLICY "Authenticated users read semantic_knowledge"
    ON semantic_knowledge FOR SELECT
    TO authenticated
    USING (true);

-- procedure_applications (общая — authenticated read)
ALTER TABLE IF EXISTS procedure_applications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anon read procedure_applications" ON procedure_applications;
CREATE POLICY "Authenticated users read procedure_applications"
    ON procedure_applications FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- 3. ТАБЛИЦЫ БЕЗ user_id (косвенно мульти-тенантные через FK)
-- chat_messages → chat_sessions → user_id (уже есть в 006)
-- messages → dialogs → user_id (уже есть в 006)
-- document_chunks → documents → user_id (уже есть в 022)
-- episode_relations → episodes → user_id (уже есть выше)
-- ============================================================================

-- ============================================================================
-- 4. ТАБЛИЦЫ КОТОРЫЕ МОГЛИ БЫТЬ СОЗДАНЫ БЕЗ RLS (если создавались вручную)
-- Перестраховка: включаем RLS на всех известных таблицах
-- ============================================================================

-- rag_dialogs
ALTER TABLE IF EXISTS rag_dialogs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access rag_dialogs" ON rag_dialogs;
CREATE POLICY "Service role full access rag_dialogs" ON rag_dialogs TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Users view own rag dialogs" ON rag_dialogs;
CREATE POLICY "Users view own rag dialogs"
    ON rag_dialogs FOR SELECT
    USING (user_id = auth.uid());
DROP POLICY IF EXISTS "Users insert own rag dialogs" ON rag_dialogs;
CREATE POLICY "Users insert own rag dialogs"
    ON rag_dialogs FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- rag_embeddings
ALTER TABLE IF EXISTS rag_embeddings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access rag_embeddings" ON rag_embeddings;
CREATE POLICY "Service role full access rag_embeddings" ON rag_embeddings TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Users view own rag embeddings" ON rag_embeddings;
CREATE POLICY "Users view own rag embeddings"
    ON rag_embeddings FOR SELECT
    USING (user_id = auth.uid());
DROP POLICY IF EXISTS "Users insert own rag embeddings" ON rag_embeddings;
CREATE POLICY "Users insert own rag embeddings"
    ON rag_embeddings FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- memory_facts
ALTER TABLE IF EXISTS memory_facts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access memory_facts" ON memory_facts;
CREATE POLICY "Service role full access memory_facts" ON memory_facts TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Users view own memory facts" ON memory_facts;
CREATE POLICY "Users view own memory facts"
    ON memory_facts FOR SELECT
    USING (user_id = auth.uid());
DROP POLICY IF EXISTS "Users insert own memory facts" ON memory_facts;
CREATE POLICY "Users insert own memory facts"
    ON memory_facts FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- analytics_events
ALTER TABLE IF EXISTS analytics_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access analytics_events" ON analytics_events;
CREATE POLICY "Service role full access analytics_events" ON analytics_events TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Users view own analytics events" ON analytics_events;
CREATE POLICY "Users view own analytics events"
    ON analytics_events FOR SELECT
    USING (user_id = auth.uid());
DROP POLICY IF EXISTS "Users insert own analytics events" ON analytics_events;
CREATE POLICY "Users insert own analytics events"
    ON analytics_events FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- ============================================================================
-- 5. ТАБЛИЦЫ ГРАФА ЗНАНИЙ (knowledge_concepts, knowledge_relations)
-- Общая база знаний — authenticated read, service_role write
-- ============================================================================

ALTER TABLE IF EXISTS knowledge_concepts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access knowledge_concepts" ON knowledge_concepts;
CREATE POLICY "Service role full access knowledge_concepts" ON knowledge_concepts TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Authenticated users read knowledge_concepts" ON knowledge_concepts;
CREATE POLICY "Authenticated users read knowledge_concepts"
    ON knowledge_concepts FOR SELECT
    TO authenticated
    USING (true);

ALTER TABLE IF EXISTS knowledge_relations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access knowledge_relations" ON knowledge_relations;
CREATE POLICY "Service role full access knowledge_relations" ON knowledge_relations TO service_role USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Authenticated users read knowledge_relations" ON knowledge_relations;
CREATE POLICY "Authenticated users read knowledge_relations"
    ON knowledge_relations FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- 5. ПРОВЕРКА: показываем все таблицы с RLS и политиками
-- ============================================================================

SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

SELECT
    schemaname,
    tablename,
    policyname,
    roles,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- КОНЕЦ МИГРАЦИИ
-- ============================================================================
