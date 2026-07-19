# Фактическое состояние системы PAD+ AI

**Дата анализа:** 18.07.2026  
**Ветка:** main  
**Цель:** Документирование реального состояния системы для корректного описания в статьях и документации

---

## 1. Pipeline (25 зарегистрированных фаз @register_phase + Anti-Loop inline; Impulse V1)

### Реальный порядок фаз (`backend/core/pipeline/executor.py`)

```python
def _build_phases(self):
    return [
        ("safety", SafetyPhase()),
        ("intent", IntentPhase()),
        ("rag", RagPhase()),
        ("knowledge_graph", KnowledgeGraphPhase()),
        ("episodic", EpisodicPhase()),
        ("semantic", SemanticPhase()),
        ("emotion", EmotionPhase()),
        ("impulse", ImpulsePhase()),                 # V1 pre-generate
        ("persona", PersonaPhase()),
        ("roots", RootsPhase()),
        ("identity", IdentityPhase()),
        ("generate", GeneratePhase()),              # + impulse_bias inject
        ("truth_loop", TruthLoopPhase()),
        ("evaluation", EvaluationPhase()),
        ("save_episode", SaveEpisodePhase()),
        ("extraction", ExtractionPhase()),
        ("emotion_update", EmotionUpdatePhase()),
        ("impulse_update", ImpulseUpdatePhase()),   # V1 single writer
        ("consolidation", None),  # встроено в execute
        ("procedure_success", None),  # встроено в execute
        ("persona_evolution", PersonaEvolutionPhase()),
        ("events_broadcast", EventsBroadcastPhase()),
        ("health", HealthMonitorPhase()),
        ("reflection", ReflectionPhase()),
        ("dreams", DreamsPhase()),
        ("metrics", MetricsPhase(self)),
        ("response_guard", ResponseGuardPhase()),
    ]
```

### Anti-Loop Guard

Выполняется **перед** основным пайплайном (`executor.py:309`):
```python
phase_result = await AntiLoopPhase(self).execute(ctx)
```

При >3 повторных запросах — блокирует выполнение.

### Итого: 25 зарегистрированных фаз (`@register_phase`, макс. `order=27`) + Anti-Loop перед циклом

**Примечание:** В v5.0 фазы зарегистрированы через декоратор `@register_phase` (не список в `_build_phases`). Anti-Loop Guard выполняется inline первым в `execute()` (вне `_build_phases`). Background-фазы (consolidation, procedure_success, persona_evolution, health, reflection, dreams, metrics) выполняются fire-and-forget через `asyncio.create_task`.

**Примечание:** Anti-Loop Guard выполняется ПЕРЕД основным пайплайном, проверяет повторяющиеся запросы и блокирует при >3 повторениях.

| Фаза | Файл | Статус |
|------|------|--------|
| anti_loop | `phases/anti_loop.py` | ✅ активна |
| safety | `phases/safety.py` | ✅ |
| intent | `phases/intent.py` | ✅ |
| rag | `phases/rag.py` | ✅ |
| knowledge_graph | `phases/knowledge_graph.py` | ✅ |
| episodic | `phases/episodic.py` | ✅ |
| semantic | `phases/semantic.py` | ✅ |
| emotion | `phases/emotion.py` | ✅ |
| impulse | `phases/impulse.py` | ✅ V1 |
| persona | `phases/persona.py` | ✅ |
| roots | `phases/roots.py` | ✅ |
| identity | `phases/identity.py` | ✅ |
| generate | `phases/generate.py` | ✅ + impulse inject |
| truth_loop | `phases/truth_loop.py` | ✅ |
| evaluation | `phases/evaluation.py` | ✅ |
| save_episode | `phases/save_episode.py` | ✅ |
| extraction | `phases/extraction.py` | ✅ |
| emotion_update | `phases/emotion_update.py` | ✅ |
| impulse_update | `phases/impulse_update.py` | ✅ V1 single writer |
| consolidation | встроено | ✅ |
| procedure_success | встроено | ✅ |
| persona_evolution | `phases/persona_evolution.py` | ✅ |
| events_broadcast | `phases/events.py` | ✅ |
| health | `phases/health.py` | ✅ |
| reflection | `phases/reflection.py` | ✅ |
| dreams | `phases/dreams.py` | ✅ |
| metrics | `phases/metrics.py` | ✅ |
| response_guard | `phases/response_guard.py` | ✅ |

---

## 2. Система памяти (7 слоёв)

| Тип памяти | Файл | Хранилище | Статус |
|------------|------|-----------|--------|
| RAG | `memory/rag.py` | PostgreSQL (pgvector) | ✅ |
| Эпизодическая | `memory/episodic.py` | SQLite | ✅ |
| Семантическая | `memory/semantic.py` | SQLite | ✅ |
| Roots | `memory/roots.py` | PostgreSQL/JSON | ✅ |
| Persona | `memory/persona.py` | PostgreSQL/JSON | ✅ |
| User Persona | `memory/user_persona.py` | PostgreSQL/JSON | ✅ |
| Memory Hygiene | `memory/hygiene.py` | — | ✅ |
| Консолидация | `memory/consolidation.py` | — | ✅ |

**Примечание:** Отдельного модуля "facts" нет. Факты хранятся в семантической памяти.

---

## 3. Emotion Engine (6 измерений)

`backend/emotion/pad_model.py:26-38`

```python
@dataclass
class EmotionState:
    # Базовые PAD параметры (-1 до +1)
    pleasure: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0
    
    # Дополнительные параметры (0 до 1)
    curiosity: float = 0.5
    confidence: float = 0.5
    social_connection: float = 0.0
```

**Статус:** ✅ Полностью соответствует описанию статьи

---

## 4. Truth Loop

`backend/core/pipeline/phases/truth_loop.py` (62 строки)

- Извлекает claims из ответа
- Проверяет через semantic memory и другие источники
- Возвращает `truth_confidence`, `claims_verified`, `add_disclaimer`

**Примечание:** Дисклеймер добавляется, но НЕ гарантируется для каждого ответа (только при low confidence).

---

## 5. X-Ray / TraceValidator

`backend/core/xray/validator.py` (397 строк)

- Валидация структуры trace
- Валидация пайплайна
- Валидация когнитивного состояния
- Детекция silent failures

**Статус:** ✅ Соответствует

---

## 6. HEALER

**Путь:** `HEALER/` (140+ файлов)

Структура:
```
HEALER/
├── healer/
│   ├── api.py
│   ├── orchestrator.py
│   ├── diagnostics/      # 9 диагностических модулей
│   ├── patcher/          # 7 паттернов
│   ├── verifier/         # 4 модуля верификации
│   └── meta/             # meta-learner
└── healer/viewer/        # Веб-интерфейс
```

**Интеграция:** `backend/integration/healer_bridge.py` — мост, релеит события в HEALER TraceStore. HealerListener подключён к TraceCollector и активен в рантайме (`backend/main.py`).

**Важно:** HEALER — отдельный проект в репозитории, интегрированный в production-пайплайн через HealerBridge (диагностика + самовосстановление по событиям TraceCollector).

**P5 (2026-07-17):**
- Default mode: `monitor` (было `suggest`)
- Новые action в RemediationEngine: `clear_cache` (очистка L1/L2), `enable_safe_mode` (strategy → simple)
- `CacheManager.clear_all()` — полная очистка L1 + L2

---

## 6.1. Living Anatomy (🧬 Anatomy)

**Файлы:** `frontend/src/pages/AnatomyPage.jsx`, `backend/api/anatomy_routes.py`, `backend/core/anatomy.py`

Интерактивная визуализация когнитивной архитектуры в реальном времени (ReactFlow). Дерево `brain` → 11 модулей (memory, reasoning, identity, emotion, reflection, dreams, truth, safety, healer, research, xray); у Memory — вложенные подмодули (episodic, semantic, rag, persona, roots).

- `GET /api/v1/anatomy` — полное дерево статусов (обновляется каждые 5с при включённом Live-режиме)
- `GET /api/v1/anatomy/{module_id}` — деталь модуля (component + decision_count для кросс-ссылки Decision Log)
- Кросс-интеграция: Anatomy ↔ Research (Decision Log по компоненту), Anatomy ↔ Snapshot (срез из Research → Snapshots)

---

## 7. Knowledge Graph

`backend/knowledge/graph.py` (367 строк)

- NetworkX-based граф
- Концепты и связи (is_a, part_of, causes, related, contradicts)
- SQLite persistence

**Статус:** ✅ Работает, но НЕ упомянут в статье

---

## 8. Impulse Core + Research (V1 runtime — 2026-07-17)

**Путь:** `backend/core/impulse/`

| Модуль | Назначение |
|--------|------------|
| `core.py` | ImpulseCore, 4 измерения, `get_bias_block()` |
| `manager.py` | Dual storage: PostgreSQL + JSON (`data/impulse.json`) |
| `deltas.py` | Единая таблица deltas + `apply_deltas()` |
| `signals.py` | Эвристический producer experience signals |
| `event_listener.py` | Observe-only (write off by default; single writer = phase) |
| `phases/impulse.py` | Pre-generate read → `impulse_bias` в ctx |
| `phases/impulse_update.py` | Post-generate apply deltas (единственный writer) |

**Интеграция:**
- GeneratePhase инжектит `impulse_bias` в system prompt
- X-Ray: `ThoughtType.IMPULSE_READ` / `IMPULSE_UPDATE`
- Compat: `scripts/impulse.py` — re-export

**Research harness (P3, 2026-07-17):**
- `backend/impulse/research.py` — автоматический прогон 5 профилей × 7 вопросов
- Keyword frequency analysis (4 словаря: understand/improve/protect/create)
- Сравнение профилей с baseline (delta, effect-size)
- `@pytest.mark.impulse_research` — не в default CI
- `experiments/I-010/` — директория для отчётов (`raw_responses.json` + `REPORT.md`)

**Research (исторические):** `experiments/I-002…I-005` — методология A/B; CI proof = unit inject без live LLM.

**Статус:** ✅ Runtime V1 реализован

### Известные баги (исправленные)

- `GET /api/v1/admin/persona/deltas` — **ImportError** (500): импорт `_IMPULSE_DELTAS` из несуществующего модуля `core.pipeline.phases.impulse_update` вместо `core.impulse.deltas`. Исправлено 18.07.2026.

---

## 9. Provider Manager

`backend/runtime/provider_manager.py`

**Поддерживаемые провайдеры:**
- OpenRouter
- GigaChat

**Fallback-логика:** OpenRouter ↔ GigaChat

**Шифрование ключей в БД** ✅

---

## 10. Chat UX (P4 — 2026-07-17)

`frontend/src/components/ChatMessage.jsx`:

- **WhyAnswerWidget** — 1-2 строки под ответом: «Стратегия: Логический анализ | Импульс: понять | Уверенность: 85%»
- **TruthBadge** — цветной индикатор: зелёный (≥0.8), жёлтый (0.5-0.8), серый (<0.5)
- **Feedback 👍/👎** — замыкается на signals.py → ImpulseUpdatePhase

`frontend/src/components/ChatControls.jsx`:
- **Preset toggle** — Strict / Balanced / Creative (POST `/api/v1/impulse/preset`)

`frontend/src/services/impulse.js`:
- `getImpulse()`, `setImpulse()`, `setImpulsePreset()` — API client

**Статус:** ✅ Chat UX (widget, badge, preset, feedback) — реализован

---

## 11. Quality & Degradation (P7 — 2026-07-17)

`backend/core/pipeline/executor.py:_mark_degraded()`:

- Каждая non-critical phase → `_mark_degraded()` + X-Ray event
- Счётчик `degradation_total` в MetricsCollector (по компоненту и severity)
- `except: pass` запрещён в critical path — проверено: 0 вхождений в backend
- Всего счётчиков: `pipeline_requests_total` + `degradation_total` → можно вычислить `% degraded`

**Статус:** ✅ Quality policy — degradation tracking, except:pass audit

---

## 12. Providers Depth (P8 — уже было)

| Компонент | Файл | Статус |
|-----------|------|--------|
| Fallback OpenRouter ↔ GigaChat | `runtime/provider_manager.py` | ✅ |
| Per-user keys + шифрование | `api/keys_routes.py` + `core/encryption.py` | ✅ |
| ModelRouter (cheap vs strong) | `core/agi/model_router.py` | ✅ |
| CognitiveBudget | `core/agi/budget.py` | ✅ |

**Статус:** ✅ Fallback, per-user keys, model router — реализованы

---

## 13. Anti-Loop Guard

`backend/core/pipeline/phases/anti_loop.py`

- Проверяет повторяющиеся запросы
- Блокирует при >3 повторениях подряд
- Trace для X-Ray

**Статус:** ✅ Работает, но НЕ упомянут в статье

---

## 11. Что НЕ найдено / не подтверждено

| Компонент | Ожидание | Ре��льность |
|-----------|----------|------------|
| Папка experiments/ | I-002 — I-005 | ❌ Не найдена |
| Impulse Core (4 измерения) | ПОНЯТЬ/УЛУЧШИТЬ/ЗАЩИТИТЬ/СОЗДАТЬ | ✅ Runtime V1 (phase + inject + update) |
| SQLite (активное хранилище) | Используется | ⚠️ Формально есть, но не основное |
| Dreams (полная реализация) | Фоновая обработка | ⚠️ Фаза есть, функциональность ограничена |

---

## 14. Итоговая статистика соответствия

| Компонент | В статье | В коде | Статус |
|-----------|----------|--------|--------|
| Pipeline фазы | 24 | 24 | ✅ Совпадает |
| Emotion Engine (6 измерений) | Да | Да | ✅ Совпадает |
| Truth Loop | Да | Да | ✅ Совпадает |
| X-Ray | Да | Да | ✅ Совпадает |
| Knowledge Graph | Нет | Да | ✅ Есть в коде |
| Anti-Loop Guard | Нет | Да | ✅ Есть в коде |
| HEALER | Отдельный проект | Отдельный проект | ✅ Совпадает |
| Impulse Core | Runtime V1 | Runtime V1 | ✅ Соответствует |
| Многоуровневая память | Да | Да | ✅ Совпадает |
| Provider Manager | OpenRouter + GigaChat | OpenRouter + GigaChat | ✅ Совпадает |

---

## 15. Рекомендации для статьи

1. **Исправить число фаз:** 24 вместо 13/22
2. **Уточнить HEALER:** "отдельный проект в репозитории" вместо "интегрирован"
3. **Убрать Impulse Research Program** или проверить актуальность
4. **Добавить Anti-Loop Guard** и Knowledge Graph
5. **Убрать SQLite** из списка активных хранилищ

---

## 16. Актуальная архитектура (фактическая)

```
┌─────────────────────────────────────────────────────────────┐
│                    PipelineExecutor v4.0                      │
├─────────────────────────────────────────────────────────────┤
│ Анти-Loop Guard → Safety → Intent → RAG → Knowledge Graph   │
│ → Episodic → Semantic → Emotion → Persona → Roots → Identity│
│ → Generate → Truth Loop → Save Episode → Emotion Update     │
│ → Consolidation → Procedure Success → Persona Evolution     │
│ → Events Broadcast → Health → Reflection → Dreams → Metrics │
│ → Response Guard                                            │
├─────────────────────────────────────────────────────────────┤
│                       Память                                  │
│  ┌─────────┐ ┌───────────┐ ┌─────────┐ ┌──────────┐        │
│  │   RAG   │ │ Эпизодич. │ │Семантич.│ │  Roots   │        │
│  │(pgvector)│ │ SQLite   │ │ SQLite  │ │PG/JSON   │        │
│  └─────────┘ └───────────┘ └─────────┘ └──────────┘        │
│  ┌─────────┐ ┌───────────┐ ┌─────────────────────┐        │
│  │ Persona │ │User Persona│ │ Memory Hygiene      │        │
│  │PG/JSON  │ │  PG/JSON  │ │ + Consolidation     │        │
│  └─────────┘ └───────────┘ └─────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                     Emotion Engine                           │
│  Pleasure, Arousal, Dominance, Curiosity, Confidence,       │
│  Social Connection                                          │
├─────────────────────────────────────────────────────────────┤
│              X-Ray + TraceValidator                          │
├─────────────────────────────────────────────────────────────┤
│                    Provider Manager                          │
│  OpenRouter + GigaChat + Fallback chains                     │
├─────────────────────────────────────────────────────────────┤
│                     HEALER (отдельный проект)                │
│  Diagnostics + Patcher + Verifier + Viewer                  │
└─────────────────────────────────────────────────────────────┘
```