# PAD+ AI — Проектный AGENTS.md (контекст для AI-ассистентов)

> Актуально на июль 2026. Синхронизировано с кодом (`backend/api/`, `frontend/src/pages/`).
> Глобальные правила работы — в `.clinerules` (в корне проекта).

## Что это
PAD+ AI — AI-ассистент с когнитивной архитектурой (PAD — Pleasure-Arousal-Dominance), памятью, RAG, Meta-Learning.
- **Домен:** https://pad-plus-ai.onrender.com
- **Бэкенд:** Python 3.11+, FastAPI, Uvicorn — порт **8007** (`os.getenv("PORT", 8007)`)
- **Фронтенд:** React 18, Vite 5, Tailwind CSS 3 — порт **5174** (`npm run dev`)
- **БД:** Supabase (PostgreSQL + Auth + Storage) в проде / SQLite локально (авто-определение через `USE_PG_STORAGE` в `backend/core/config.py`)
- **Хостинг:** Render (веб-сервис, авто-деплой из `main`)
- **Провайдеры LLM:** пользовательские ключи OpenRouter и GigaChat (системных ключей нет). Ключи шифруются (Fernet), очищаются от не-ASCII (`\xa0`) при сохранении/чтении.

## Структура бэкенда (реальная)
Роутеры живут в **`backend/api/`** (НЕ в `backend/app/routers/` — этот путь больше не используется). Регистрация в `backend/main.py` → `_register_routers()`.

| Префикс | Файл | Назначение |
|---------|------|-----------|
| `/api/v1` | `frontend_routes.py`, `routes.py`, `document_routes.py` | Фронт-API (auth, chat, mind-state, health, providers, keys, documents, collections) |
| `/api/v1/user` | `user_routes.py` | Пользователи + `/keys` (API-ключи) |
| `/api/v1/dialogs` | `dialog_routes.py` | История диалогов |
| `/api/v1/xray` | `xray_routes.py` | X-Ray наблюдаемость |
| `/api/v1/metrics` | `metrics_routes.py` | Метрики pipeline/системы |
| `/api/v1/memory` | `memory_routes.py` | Memory-дашборд |
| `/api/v1/knowledge` | `knowledge_routes.py` | Граф знаний |
| `/api/v1/feedback` | `feedback_routes.py` | Обратная связь |
| `/api/v1/healer` | `healer_routes.py` | HEALER |
| `/api/v1/experience` | `experience_routes.py` | Опыт (`/admin/experiences`) |
| `/api/v1/admin/persona` | `persona_routes.py` | Persona (admin) |
| `/api/v1/impulse` | `impulse_routes.py` | Impulse Core |
| `/api/v1/admin` | `admin_routes.py` | Admin (emotion, sync, health) |
| `/api/v1/sentry` | `sentry_routes.py` | Sentry-совместимый ingest |
| `/api/v1/experiments` | `experiments_routes.py` | Research Platform (runs/compare/evals/snapshots) |
| `/api/v1/decisions` | `decisions_routes.py` | Decision Log |
| `/api/v1/anatomy` | `anatomy_routes.py` | 🧬 Живая анатомия (`get_module_status`, `get_module_detail`) |
| `/api/v1/learning` | `learning_routes.py` | Обучение |
| `/api/v1/debug` | `debug_routes.py` | Только при `DEBUG=true` |

> ℹ️ Ранее существовавший `legacy_routes.py` (заглушки 503 для `/providers` и `/keys`) **удалён** — он был мёртвым кодом, не регистрировался в `main.py` и создавал риск перекрытия рабочих эндпоинтов при случайном подключении.

## Структура фронтенда
Hash-навигация (`#<id>`), страницы в `frontend/src/pages/`, табы в `frontend/src/App.jsx`.

| Hash | Файл | Назначение |
|------|------|-----------|
| `#home` | `DashboardPage.jsx` | Дашборд |
| `#chat` | `ChatPage.jsx` | Чат с LLM (stream + вложения) |
| `#anatomy` | `AnatomyPage.jsx` | 🧬 Живая анатомия (ReactFlow, дерево модулей) |
| `#research` | `ResearchPage.jsx` + `research/` | 🔬 Research (7 вкладок: Runs, Compare, Decisions, X-Ray, Metrics, Eval, Pipeline) |
| `#xray` | `XRayPage.jsx` | Трассировка pipeline |
| `#healer` | `HealerPage.jsx` | Самовосстановление |
| `#knowledge` | `KnowledgePage.jsx` | Граф знаний (ReactFlow) |
| `#memory` | `MemoryPage.jsx` | Memory-дашборд |
| `#experience` | `ExperiencePage.jsx` | Опыт и дельты |
| `#history` | `HistoryPage.jsx` | История диалогов |
| `#documents` | `DocumentsPage.jsx` | Документы |
| `#providers` | `ProvidersPage.jsx` | Провайдеры/ключи |
| `#connected-providers` | `ConnectedProvidersPage.jsx` | Подключённые ключи |
| `#settings` | `SettingsPage.jsx` | Настройки |
| `#instructions` | `InstructionsPage.jsx` | Инструкции (вкладки по подсистемам) |

**Кросс-интеграции:**
- 🧬 Anatomy ↔ 🔬 Research: кнопка «Решения модуля» → `#research?component=<component>` (фильтр Decision Log через `decisions_routes.py`).
- 🧬 Anatomy ↔ Snapshot: `#anatomy?snapshot=<id>` показывает срез снэпшота из Research.

## Pipeline (v5.0)
`backend/core/pipeline/executor.py` — **25 зарегистрированных фаз** через декоратор `@register_phase` (макс. `order=27`) + **AntiLoopPhase** inline (первым, вне `_build_phases`).

- **Sync path (hot):** anti_loop → safety → intent → rag → knowledge_graph → episodic → semantic → emotion → impulse → persona → roots → identity → generate → truth_loop → evaluation → save_episode → extraction → emotion_update → impulse_update → events_broadcast → response_guard
- **Background path (fire-and-forget, `asyncio.create_task`):** consolidation, procedure_success, persona_evolution, health, reflection, dreams, metrics

`get_stats()` возвращает `version = "5.0"`.

## Память (7 типов)
`backend/memory/`: `rag.py` (pgvector), `episodic.py`, `semantic.py` (факты внутри), `roots.py`, `persona.py`, `user_persona.py`, `hygiene.py`, `consolidation.py`.

## Эмоции (PAD+)
`backend/emotion/pad_model.py` — 6 измерений: pleasure, arousal, dominance (-1..+1), curiosity, confidence, social_connection (0..1). Затухание ~0.001/сек.

## X-Ray
`backend/core/xray/` — `trace_collector.py`, `broadcaster.py` (WebSocket), `meta_learner.py`, `thought_visualizer.py`, `history_recorder.py`. HealerListener подписан на TraceCollector.

## HEALER
Отдельный проект `HEALER/` + интеграция `backend/integration/healer_bridge.py`. HealerListener активен в рантайме (production-интеграция). Режимы: monitor / suggest / auto.

## Living Anatomy
`backend/core/anatomy.py` агрегирует live-статус: `brain` → 11 модулей (memory, reasoning, identity, emotion, reflection, dreams, truth, safety, healer, research, xray); у Memory вложенные подмодули (episodic, semantic, rag, persona, roots). Кросс-ссылка модуль → компонент Decision Log через `MODULE_TO_COMPONENT`.

## Запуск
```bash
# Backend (локально, SQLite)
cd backend && uvicorn main:app --reload --port 8007

# Frontend
cd frontend && npm run dev   # http://localhost:5174
```
Swagger UI: http://localhost:8007/docs

## Документация
Актуальная — в `docs/`: `ARCHITECTURE.md`, `PROJECT_STRUCTURE.md`, `RELEASE_v4.0.md`, `ACTUAL_STATE.md`, `API.md` (переписан под `backend/api/`), `XRAY.md`, `HEALER.md`, `architecture/` (детально).
