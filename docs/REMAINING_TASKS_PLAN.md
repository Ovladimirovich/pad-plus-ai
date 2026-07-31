# План выполнения оставшихся задач из ARCHITECTURE_EVOLUTION_PLAN.md

## Фаза A: Architecture Cleanup (остальное)

### A1: Fix `execution_time_ms` — write before EvaluationPhase reads it

**Проблема:** `execution_time_ms` читается EvaluationPhase, но не пишется в PipelineContext.

**Анализ (выполняется):**
- [ ] `grep "execution_time_ms" backend/core/pipeline/` — найти все использования
- [ ] Определить где должно писаться значение (в executor.py перед EvaluationPhase)

**Шаги:**
1. [ ] Найти все использования `execution_time_ms` в pipeline
2. [ ] Добавить запись `ctx.execution_time_ms` в `executor.py` перед EvaluationPhase
3. [ ] Добавить тест в `tests/test_pipeline/test_evaluation.py`

**Оценка:** 0.5 дня

---

### A2: Fix `procedure_used` — align key name between SemanticPhase and SaveEpisodePhase

**Проблема:** SemanticPhase пишет `procedure_used`, SaveEpisodePhase читает другой ключ.

**Шаги:**
1. [ ] Найти запись в SemanticPhase и чтение в SaveEpisodePhase
2. [ ] Согластовать имена ключей (выбрать одно: `procedure_used` или `procedure`)
3. [ ] Добавить тест в `tests/test_pipeline/test_save_episode.py`

**Оценка:** 0.5 дня

---

### A3: Fix `result_dict` — write before ReflectionPhase reads it

**Проблема:** `result_dict` читается ReflectionPhase, но не пишется.

**Шаги:**
1. [ ] Найти все использования `result_dict` в pipeline
2. [ ] Добавить запись в `PipelineContext` перед ReflectionPhase
3. [ ] Добавить тест в `tests/test_pipeline/test_reflection.py`

**Оценка:** 0.5 дня

---

### A4: Register MemoryMaintenancePhase or remove it

**Анализ:**
- [ ] `grep "MemoryMaintenancePhase" backend/` — найти определение
- [ ] Проверить: зарегистрирован в pipeline registry?

**Шаги:**
1. [ ] Если нужен — добавить в `_build_phases()` в `executor.py`
2. [ ] Если не нужен — удалить `backend/core/pipeline/phases/memory_maintenance.py`
3. [ ] Обновить тесты

**Оценка:** 0.5 дня

---

### A5: Fix MemoryHygiene — execute actual deletions or remove simulation

**Анализ:**
- [ ] `grep "run_cleanup" backend/memory/` — найти метод
- [ ] Проверить: удаляет ли он реально или только симулирует

**Шаги:**
1. [ ] Найти `MemoryHygiene.run_cleanup()`
2. [ ] Добавить реальное удаление дубликатов
3. [ ] Или удалить симуляцию и метод

**Оценка:** 0.5 дня

---

### A6: Remove PersonaMemory.users — single SOF for per-user state

**Проблема:** `PersonaMemory.users` дублирует `UserPersona`, два независимых пути обновления.

**Шаги:**
1. [ ] Найти все использования `PersonaMemory.users`
2. [ ] Перенаправить на `UserPersona`
3. [ ] Удалить `PersonaMemory.users`
4. [ ] Обновить тесты в `tests/test_pipeline/test_persona*.py`

**Оценка:** 2-3 дня

---

## Фаза C: Session Isolation (остальное)

### C1: Unified session identity — один session_id для всех подсистем

**Проблема:** session_id, dialog_id, JWT, request_id — 4+ системы управляют identity по-разному.

**Шаги:**
1. [ ] Определить canonical `session_id` source (SessionManager?)
2. [ ] Создать `SessionIdentityProvider` singleton
3. [ ] Обновить все подсистемы: SessionManager, X-Ray, Emotion, Impulse
4. [ ] Добавить тест: 100 concurrent sessions, no cross-contamination

**Оценка:** 3-4 дня

---

### C3: ImpulseCore scoped per-session

**Проблема:** ImpulseCore — global singleton, state leaks между пользователями.

**Шаги:**
1. [ ] Создать `ImpulseSessionStore` (аналогично `SessionEmotionStore`)
2. [ ] Мигрировать все callers `get_impulse_core()` на `store.get_or_create(session_id)`
3. [ ] Добавить TTL + LRU eviction
4. [ ] Добавить тест: User A "understand" weight doesn't leak to User B

**Оценка:** 3-4 дня

---

### C4: SessionManager deduplicate with Supabase auth sessions

**Проблема:** SessionManager и Supabase управляют lifecycle независимо.

**Шаги:**
1. [ ] Найти два независимых lifecycle session management
2. [ ] Объединить — использовать Supabase как source of truth
3. [ ] SessionManager становится кэшем over Supabase
4. [ ] Добавить тест: session lifecycle consistency

**Оценка:** 2-3 дня

---

## Порядок выполнения

1. **A1, A2, A3** — блокери для Phase B (pipeline stabilization) — высший приоритет
2. **A6** — блокери для C1 — высший приоритет
3. **A4, A5** — cleanup, можно параллельно с A1-A3
4. **C1** — после A6
5. **C3, C4** — после C1

## Оценка времени

| Задача | Оценка | Приоритет |
|--------|--------|-----------|
| A1 | 0.5 дня | High |
| A2 | 0.5 дня | High |
| A3 | 0.5 дня | High |
| A4 | 0.5 дня | Medium |
| A5 | 0.5 дня | Medium |
| A6 | 2-3 дня | High |
| C1 | 3-4 дня | High |
| C3 | 3-4 дня | High |
| C4 | 2-3 дня | Medium |
| **Итого** | **~2 недели** | |

## Критерии успеха

- **После A1-A3:** `PipelineContext` имеет `execution_time_ms`, `procedure_used`, `result_dict` корректно
- **После A4:** Нет orphaned phases в pipeline registry
- **После A5:** `MemoryHygiene.run_cleanup()` удаляет реально или удалён
- **После A6:** `PersonaMemory.users` удалён, `UserPersona` — единственный SOF
- **После C1:** Один canonical `session_id` для всех подсистем
- **После C3:** ImpulseCore scoped per-session, no cross-contamination
- **После C4:** SessionManager и Supabase используют единый lifecycle
- **Тесты:** 380+ passing, 0 regressions
