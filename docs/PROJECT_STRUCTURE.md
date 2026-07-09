# 📁 Структура проекта PAD+ AI

**Версия:** 3.0  
**Последнее обновление:** Июль 2026  
**Статус:** ✅ Актуально (по фактическому состоянию кода)

---

## Обзор

```
PAD+ AI/
├── backend/                    # Python backend (FastAPI)
├── frontend/                   # React frontend (Vite)
├── docs/                       # Документация
├── tests/                      # Тесты
├── HEALER/                     # HEALER (отдельный проект, диагностика)
└── data/                       # Локальные данные (SQLite, JSON)
```

---

## Backend (`backend/`)

### Pipeline (`backend/core/pipeline/`)

**Executor:** `executor.py` — PipelineExecutor v4.0, 24 именованные фазы.

**Фазы** (`phases/`):

| Файл | Назначение |
|------|------------|
| `anti_loop.py` | Anti-Loop Guard (перед пайплайном) |
| `safety.py` | Проверка безопасности |
| `intent.py` | Классификация намерения |
| `rag.py` | RAG поиск (pgvector) |
| `knowledge_graph.py` | Граф знаний (NetworkX) |
| `episodic.py` | Эпизодическая память |
| `semantic.py` | Семантическая память |
| `emotion.py` | Emotion Engine (PAD+) |
| `persona.py` | Persona личность |
| `roots.py` | Roots фундаментальные принципы |
| `identity.py` | Перехват вопросов об идентичности |
| `generate.py` | Генерация ответа LLM |
| `truth_loop.py` | Проверка утверждений |
| `save_episode.py` | Сохранение эпизода |
| `emotion_update.py` | Обновление эмоционального состояния |
| `persona_evolution.py` | Эволюция личности |
| `events.py` | Events Broadcast |
| `health.py` | Health Monitor |
| `reflection.py` | Reflection Loop |
| `dreams.py` | Dreams (фоновая обработка) |
| `metrics.py` | Сбор метрик |
| `response_guard.py` | Финальная проверка ответа |

### Модули памяти (`backend/memory/`)

| Модуль | Хранилище | Назначение |
|--------|-----------|------------|
| `rag.py` | PostgreSQL (pgvector) | Векторный поиск по документам |
| `episodic.py` | SQLite | История диалогов |
| `semantic.py` | SQLite | Типизированные знания |
| `roots.py` | PostgreSQL/JSON | Фундаментальные принципы |
| `persona.py` | PostgreSQL/JSON | Личность системы |
| `user_persona.py` | PostgreSQL/JSON | Модель пользователя |
| `hygiene.py` | — | Гигиена памяти |
| `consolidation.py` | — | Консолидация в долгосрочную |

**Примечание:** Отдельного модуля "facts" нет. Факты хранятся в семантической памяти.

### Эмоциональная модель (`backend/emotion/`)

`pad_model.py` — 6-мерная модель PAD+:

- **Базовые PAD:** pleasure, arousal, dominance (-1 до +1)
- **Дополнительные:** curiosity, confidence, social_connection (0 до 1)

### X-Ray система (`backend/core/xray/`)

| Файл | Назначение |
|------|------------|
| `validator.py` | TraceValidator — валидация трассировок |
| `trace_collector.py` | Сбор trace событий |
| `broadcaster.py` | WebSocket broadcaster |
| `healing_detectors.py` | Детекторы проблем |

### Provider Management (`backend/runtime/`)

| Файл | Назначение |
|------|------------|
| `provider_manager.py` | ProviderManager + fallback-цепочки |
| `llm_service.py` | Единый интерфейс LLM |
| `gigachat_client.py` | GigaChat SDK |

---

## HEALER (отдельный проект)

**Путь:** `HEALER/`

Структура:
```
HEALER/
├── healer/
│   ├── api.py
│   ├── orchestrator.py
│   ├── diagnostics/      # 9 модулей
│   ├── patcher/          # 7 паттернов
│   ├── verifier/         # 4 модуля
│   └── meta/             # meta-learner
└── healer/viewer/        # Веб-интерфейс
```

**Интеграция:** `backend/integration/healer_bridge.py` — релеит события в HEALER TraceStore.

**Важно:** HEALER — отдельный проект, НЕ интегрирован в production-пайплайн. Используется для диагностики и самовосстановления.

---

## Тесты (`tests/`)

| Категория | Количество | Директория |
|-----------|------------|------------|
| Pipeline фазы | 49 | `test_pipeline/` |
| X-Ray | 14 | `test_xray/` |
| Hardening | 225 | `hardening/` |
| Интеграционные | ~10 | `integration/` |

---

## Документация (`docs/`)

| Файл | Описание |
|------|----------|
| `ACTUAL_STATE.md` | Фактическое состояние системы (июль 2026) |
| `ARCHITECTURE.md` | Архитектура системы |
| `API.md` | API спецификация |
| `PROJECT_STRUCTURE.md` | Этот файл |
| `RELEASE_v4.0.md` | Релиз v4.0 |
| `XRAY.md` | X-Ray система |
| `architecture/` | Детальная архитектура |

---

## Ключевые метрики

| Метрика | Значение |
|---------|----------|
| **Backend файлов** | 100+ |
| **Frontend файлов** | 50+ |
| **Тестов** | 400+ |
| **Pipeline фаз** | 24 + Anti-Loop |
| **Слоёв памяти** | 7 |

---

## Что отсутствует / не найдено

| Ожидаемое | Факт |
|-----------|------|
| `experiments/` (I-002 — I-005) | Не найдено |
| Полный Impulse Core (4 измерения) | Базовый event listener только |
| SQLite как активное хранилище | Формально есть, не основное |

---

## Актуальная архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    PipelineExecutor v4.0                      │
├─────────────────────────────────────────────────────────────┤
│ 24 фазы: Anti-Loop → Safety → Intent → RAG → Knowledge Graph│
│ → Episodic → Semantic → Emotion → Persona → Roots → Identity│
│ → Generate → Truth Loop → Save Episode → Emotion Update     │
│ → Persona Evolution → Events Broadcast → Health → Reflection│
│ → Dreams → Metrics → Response Guard                         │
├─────────────────────────────────────────────────────────────┤
│                       Память (7 слоёв)                        │
│  RAG (pgvector) | Episodic | Semantic | Roots | Persona |    │
│  User Persona | Hygiene + Consolidation                      │
├─────────────────────────────────────────────────────────────┤
│                     Emotion Engine (6 измерений)             │
├─────────────────────────────────────────────────────────────┤
│              X-Ray + TraceValidator + Healing               │
├─────────────────────────────────────────────────────────────┤
│                    Provider Manager                          │
│  OpenRouter | GigaChat | Fallback chains                     │
├─────────────────────────────────────────────────────────────┤
│              HEALER (отдельный проект, диагностика)          │
└─────────────────────────────────────────────────────────────┘
```