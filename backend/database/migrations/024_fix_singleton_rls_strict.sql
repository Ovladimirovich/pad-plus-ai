-- ============================================================================
-- PAD+ AI v4.0 — Строгие RLS политики для singleton-таблиц
-- ============================================================================
-- Проблема: Supabase Security Advisor (lint 0013) требует RLS на всех
-- таблицах в public схеме. Предыдущая миграция (023) включила RLS, но
-- оставила политику TO anon USING (true), которая не защищает реально.
--
-- Этот скрипт:
-- 1. Меняет политики singleton-таблиц на строгие: разрешён доступ
--    ТОЛЬКО к строке id = 'system'
-- 2. roots_knowledge — меняет с anon read на authenticated read
-- ============================================================================

-- ============================================================================
-- 1. persona_state — singleton (одна строка id='system')
-- ============================================================================
ALTER TABLE IF EXISTS persona_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anon read persona_state" ON persona_state;
DROP POLICY IF EXISTS "Service role full access persona_state" ON persona_state;

CREATE POLICY "service_role_all_persona_state"
    ON persona_state
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "read_singleton_persona_state"
    ON persona_state
    FOR SELECT
    TO anon, authenticated
    USING (id = 'system');

-- ============================================================================
-- 2. emotion_state — singleton (одна строка id='system')
-- ============================================================================
ALTER TABLE IF EXISTS emotion_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anon read emotion_state" ON emotion_state;
DROP POLICY IF EXISTS "Service role full access emotion_state" ON emotion_state;

CREATE POLICY "service_role_all_emotion_state"
    ON emotion_state
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "read_singleton_emotion_state"
    ON emotion_state
    FOR SELECT
    TO anon, authenticated
    USING (id = 'system');

-- ============================================================================
-- 3. impulse_state — singleton (одна строка id='system')
-- ============================================================================
ALTER TABLE IF EXISTS impulse_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anon read impulse_state" ON impulse_state;
DROP POLICY IF EXISTS "Service role full access impulse_state" ON impulse_state;

CREATE POLICY "service_role_all_impulse_state"
    ON impulse_state
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "read_singleton_impulse_state"
    ON impulse_state
    FOR SELECT
    TO anon, authenticated
    USING (id = 'system');

-- ============================================================================
-- 4. roots_knowledge — коллекция (НЕ singleton), общие данные для всех юзеров
--    Меняем anon read → authenticated read
-- ============================================================================
ALTER TABLE IF EXISTS roots_knowledge ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anon read roots_knowledge" ON roots_knowledge;
DROP POLICY IF EXISTS "Service role full access roots_knowledge" ON roots_knowledge;

CREATE POLICY "service_role_all_roots_knowledge"
    ON roots_knowledge
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "read_roots_knowledge"
    ON roots_knowledge
    FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- 5. ПРОВЕРКА — показываем обновлённые политики
-- ============================================================================

SELECT
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('persona_state', 'emotion_state', 'impulse_state', 'roots_knowledge')
ORDER BY tablename, policyname;

-- ============================================================================
-- КОНЕЦ МИГРАЦИИ
-- ============================================================================
