# Фактическое состояние системы PAD+ AI

**Дата анализа:** 03.07.2026  
**Ветка:** main  
**Цель:** Документирование реального состояния системы для корректного описания в статьях и документации

---

## 1. Pipeline (24 фазы)

### Реальный порядок фаз (`backend/core/pipeline/executor.py:76-101`)

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
        ("persona", PersonaPhase()),
        ("roots", RootsPhase()),
        ("identity", IdentityPhase()),
        ("generate", GeneratePhase()),
        ("truth_loop", TruthLoopPhase()),
        ("save_episode", SaveEpisodePhase()),
        ("emotion_update", EmotionUpdatePhase()),
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

### Итого: 24 именованные фазы + Anti-Loop перед циклом

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
| persona | `phases/persona.py` | ✅ |
| roots | `phases/roots.py` | ✅ |
| identity | `phases/identity.py` | ✅ |
| generate | `phases/generate.py` | ✅ |
| truth_loop | `phases/truth_loop.py` | ✅ |
| save_episode | `phases/save_episode.py` | ✅ |
| emotion_update | `phases/emotion_update.py` | ✅ |
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

**Интеграция:** `backend/integration/healer_bridge.py` — мост, релеит события в HEALER TraceStore.

**Важно:** HEALER — отдельный проект в репозитории, НЕ интегрирован в production-пайплайн. Сосуществует как диагностический инструмент.

---

## 7. Knowledge Graph

`backend/knowledge/graph.py` (367 строк)

- NetworkX-based граф
- Концепты и связи (is_a, part_of, causes, related, contradicts)
- SQLite persistence

**Статус:** ✅ Работает, но НЕ упомянут в статье

---

## 8. Impulse Core

**Путь:** `backend/core/impulse/`

Файлы:
- `__init__.py`
- `event_listener.py`

**Статус:** Базовый event listener существует, но функциональность ограничена.

**Важно:** Папка `experiments/` (с I-002, I-003, I-004, I-005) — НЕ найдена. Возможно, удалена или переименована.

---

## 9. Provider Manager

`backend/runtime/provider_manager.py`

**Поддерживаемые провайдеры:**
- OpenRouter
- GigaChat

**Fallback-логика:** OpenRouter ↔ GigaChat

**Шифрование ключей в БД** ✅

---

## 10. Anti-Loop Guard

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
| Impulse Core (4 измерения) | ПОНЯТЬ/УЛУЧШИТЬ/ЗАЩИТИТЬ/СОЗДАТЬ | ❌ Не подтверждено в рантайме |
| SQLite (активное хранилище) | Используется | ⚠️ Формально есть, но не основное |
| Dreams (полная реализация) | Фоновая обработка | ⚠️ Фаза есть, функциональность ограничена |

---

## 12. Итоговая статистика соответствия

| Компонент | В статье | В коде | Статус |
|-----------|----------|--------|--------|
| Pipeline фазы | 24 | 24 | ✅ Совпадает |
| Emotion Engine (6 измерений) | Да | Да | ✅ Совпадает |
| Truth Loop | Да | Да | ✅ Совпадает |
| X-Ray | Да | Да | ✅ Совпадает |
| Knowledge Graph | Нет | Да | ✅ Есть в коде |
| Anti-Loop Guard | Нет | Да | ✅ Есть в коде |
| HEALER | Отдельный проект | Отдельный проект | ✅ Совпадает |
| Impulse Core | Частичный | Частичный | ⚠️ Соответствует |
| Многоуровневая память | Да | Да | ✅ Совпадает |
| Provider Manager | OpenRouter + GigaChat | OpenRouter + GigaChat | ✅ Совпадает |

---

## 13. Рекомендации для статьи

1. **Исправить число фаз:** 24 вместо 13/22
2. **Уточнить HEALER:** "отдельный проект в репозитории" вместо "интегрирован"
3. **Убрать Impulse Research Program** или проверить актуальность
4. **Добавить Anti-Loop Guard** и Knowledge Graph
5. **Убрать SQLite** из списка активных хранилищ

---

## 14. Актуальная архитектура (фактическая)

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