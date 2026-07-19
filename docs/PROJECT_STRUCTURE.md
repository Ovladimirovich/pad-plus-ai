# 📁 Структура проекта PAD+ AI

**Версия:** 4.0  
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

**Executor:** `executor.py` — PipelineExecutor v5.0 (Hot/Background split). 25 зарегистрированных фаз (`@register_phase`, макс. `order=27`) + AntiLoopPhase выполняется inline перед циклом.

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

### API роутеры (`backend/api/`)

Регистрируются в `backend/main.py` → `_register_routers()`. **Важно:** старая структура `backend/app/routers/` больше не используется.

| Файл | Префикс | Назначение |
|------|---------|-----------|
| `frontend_routes.py` | `/api/v1` | Фронт-API (health, mind-state, providers) |
| `routes.py` | `/api/v1` | Корневые эндпоинты |
| `document_routes.py` | `/api/v1` | Управление документами |
| `user_routes.py` | `/api/v1/user` | Пользователи + `/keys` (API-ключи) |
| `dialog_routes.py` | `/api/v1/dialogs` | История диалогов |
| `xray_routes.py` | `/api/v1/xray` | X-Ray наблюдаемость |
| `metrics_routes.py` | `/api/v1/metrics` | Метрики pipeline/системы |
| `memory_routes.py` | `/api/v1/memory` | Memory-дашборд |
| `knowledge_routes.py` | `/api/v1/knowledge` | Граф знаний |
| `feedback_routes.py` | `/api/v1/feedback` | Обратная связь |
| `healer_routes.py` | `/api/v1/healer` | HEALER |
| `experience_routes.py` | `/api/v1/admin/experiences` | Опыт |
| `persona_routes.py` | `/api/v1/admin/persona` | Persona (admin) |
| `impulse_routes.py` | `/api/v1/impulse` | Impulse Core |
| `admin_routes.py` | `/api/v1/admin` | Admin |
| `sentry_routes.py` | `/api/v1/sentry` | Sentry-совместимый ingest |
| `experiments_routes.py` | `/api/v1/experiments` | Research Platform (runs/compare/evals) |
| `decisions_routes.py` | `/api/v1/decisions` | Decision Log |
| `anatomy_routes.py` | `/api/v1/anatomy` | 🧬 Живая анатомия |
| `learning_routes.py` | `/api/v1/learning` | Обучение |
| `debug_routes.py` | `/api/v1/debug` | Только при `DEBUG=true` |

### Living Anatomy (`backend/core/anatomy.py`)

Агрегатор live-статуса всех когнитивных модулей. Возвращает дерево `brain` → 11 модулей (memory, reasoning, identity, emotion, reflection, dreams, truth, safety, healer, research, xray); у Memory — вложенные подмодули (episodic, semantic, rag, persona, roots). Каждый узел содержит `status`, `metrics`, `children`. Кросс-ссылка модуль → компонент Decision Log через `MODULE_TO_COMPONENT`.

---

## HEALER (отдельный проект + интеграция)

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

**Интеграция:** `backend/integration/healer_bridge.py` — релеит события в HEALER TraceStore. HealerListener подключён к TraceCollector и активен в рантайме (`backend/main.py`). HEALER используется для диагностики и самовосстановления и интегрирован в production-пайплайн через HealerBridge.

---

## Frontend (`frontend/`)

React + Vite, hash-навигация (`#<id>`). Страницы в `frontend/src/pages/`:

| Файл | Hash | Назначение |
|------|------|-----------|
| `DashboardPage.jsx` | `#home` | Главный дашборд |
| `ChatPage.jsx` | `#chat` | Чат с LLM |
| `AnatomyPage.jsx` | `#anatomy` | 🧬 Живая анатомия (ReactFlow) |
| `ResearchPage.jsx` + `research/` | `#research` | 🔬 Research (7 вкладок) |
| `XRayPage.jsx` | `#xray` | Трассировка pipeline |
| `HealerPage.jsx` | `#healer` | Самовосстановление |
| `KnowledgePage.jsx` | `#knowledge` | Граф знаний |
| `MemoryPage.jsx` | `#memory` | Memory-дашборд |
| `ExperiencePage.jsx` | `#experience` | Опыт и дельты |
| `HistoryPage.jsx` | `#history` | История диалогов |
| `DocumentsPage.jsx` | `#documents` | Документы |
| `ProvidersPage.jsx` | `#providers` | Провайдеры/ключи |
| `ConnectedProvidersPage.jsx` | `#connected-providers` | Подключённые ключи |
| `SettingsPage.jsx` | `#settings` | Настройки |
| `InstructionsPage.jsx` | `#instructions` | Инструкции (вкладки по подсистемам) |

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
| **Pipeline фаз** | 25 (`@register_phase`) + Anti-Loop inline |
| **Слоёв памяти** | 7 |
| **Фронтенд-страниц** | 15 |
| **Бэкенд-роутеров** | 18 (в `backend/api/`) |

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
│ 25 фаз: Anti-Loop → Safety → Intent → RAG → Knowledge Graph │
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