# 🏗️ PAD+ AI v4.0 — Архитектура

## Обзор

PAD+ AI — **когнитивный слой** с эмоциями, памятью и автономными процессами для любого LLM.

*PAD+ = Pleasure, Arousal, Dominance + Curiosity, Confidence, Social Connection*

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                      │
│  Порт: 5174 | Tailwind CSS | Supabase Auth                      │
│  Чат | Провайдеры | Дашборд | Anatomy | Research | Knowledge    │
│  Experience | Healer | X-Ray | История | Документы | Настройки  │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTP + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  Порт: 8007 | 18 routers (backend/api/*.py) | Supabase (PG)     │
│  Auth | Keys | Chat | Providers | Memory | Anatomy | X-Ray      │
└────────────────────────────┬────────────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────────────┐
│                   PROVIDER MANAGER                               │
│         Единый интерфейс к LLM провайдерам                       │
│  GigaChat | OpenRouter | Groq | Google | Anthropic              │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline v5.0 — 24 фазы (Hot/Background split)

```
User Message
     │
     ▼
┌──────────────────────┐
│  1. AntiLoopGuard    │ ← Защита от повторения (inline)
├──────────────────────┤
│  2. Safety           │ ← Проверка безопасности
├──────────────────────┤
│  3. Intent           │ ← Классификация намерения
├──────────────────────┤
│  ┌────────────────┐  │
│  │ 4. RAG         │  │ ← Параллельная группа
│  │ 5. Knowledge   │  │
│  │    Graph       │  │
│  │ 6. Episodic    │  │
│  │ 7. Semantic    │  │
│  │ 8. Emotion     │  │
│  └────────────────┘  │
├──────────────────────┤
│  9. Impulse (read)   │ ← Bias injection в system prompt
├──────────────────────┤
│ 10. Persona          │ ← Контекст личности
├──────────────────────┤
│ 11. Roots            │ ← Фундаментальные принципы
├──────────────────────┤
│ 12. Identity         │ ← Системный промпт + providers
├──────────────────────┤
│ 13. Generate         │ ← LLM вызов (GigaChat/OpenRouter)
├──────────────────────┤
│ 14. TruthLoop        │ ← Верификация утверждений
├──────────────────────┤
│ 15. Evaluation       │ ← Самооценка (4 критерия)
├──────────────────────┤
│ 16. SaveEpisode      │ ← Сохранение эпизода в память
├──────────────────────┤
│ 17. Extraction       │ ← Извлечение сущностей
├──────────────────────┤
│ 18. EmotionUpdate    │ ← Обновление эмоций
├──────────────────────┤
│ 19. ImpulseUpdate    │ ← Запись дельт импульса
├──────────────────────┤
│ 20. EventsBroadcast  │ ← События (dialogue_completed)
├──────────────────────┤
│ 21. ResponseGuard    │ ← Финальная фильтрация ответа
└──────────┬───────────┘
           │ Ответ пользователю
           ▼
    ┌──────┴──────┐
    │  RESPONSE   │ ◄─── Sync path (await)
    └─────────────┘
           │
           ▼  (fire-and-forget via asyncio.create_task)
    ┌──────────────────┐
    │ BACKGROUND PHASES│
    ├──────────────────┤
    │ Consolidation    │ ← Сжатие памяти
    │ ProcedureSuccess │ ← Успех процедуры
    │ PersonaEvolution │ ← Эволюция личности
    │ Health           │ ← Мониторинг здоровья
    │ Reflection       │ ← Рефлексия
    │ Dreams           │ ← Сны (консолидация)
    │ Metrics          │ ← Аналитика
    └──────────────────┘
```

### Фазы Impulse Core

| # | Фаза | Направление | Описание |
|---|------|------------|----------|
| 9 | ImpulsePhase | pre-generate read | Инжектит impulse_bias в system prompt |
| 19 | ImpulseUpdatePhase | post-generate write | Записывает дельты на основе опыта |

**4 измерения импульса:** understand, improve, protect, create (Pleasure-Arousal-Dominance + Meta)

## Фронтенд — страницы (hash-навигация)

Все страницы зарегистрированы в `frontend/src/App.jsx` (массив `tabs`) и открываются по hash (`#<id>`):

| Hash | Страница | Назначение |
|------|----------|-----------|
| `#home` | Dashboard | Главный дашборд системы |
| `#chat` | Chat | Чат с LLM (stream + вложения) |
| `#anatomy` | 🧬 Anatomy | Живая анатомия когнитивной архитектуры (дерево модулей в реальном времени) |
| `#research` | 🔬 Research | Исследовательская платформа (7 вкладок: Runs, Compare, Decisions, X-Ray, Metrics, Eval, Pipeline) |
| `#xray` | X-Ray | Трассировка pipeline в реальном времени |
| `#healer` | Healer | Самовосстановление (HEALER) |
| `#knowledge` | Knowledge | Граф знаний (ReactFlow) |
| `#memory` | Memory | Memory-дашборд |
| `#experience` | Experience | Опыт и дельта-коэффициенты |
| `#history` | History | История диалогов |
| `#documents` | Documents | Документы |
| `#providers` | Providers | Управление провайдерами/ключами |
| `#connected-providers` | Connected Providers | Подключённые ключи |
| `#settings` | Settings | Настройки |
| `#instructions` | Instructions | Инструкции (вкладки по каждой подсистеме) |

**Кросс-интеграции:**
- 🧬 Anatomy ↔ 🔬 Research: кнопка «Решения модуля» в детали узла → `#research?component=<component>` (фильтр Decision Log).
- 🧬 Anatomy ↔ 🔬 Research (Snapshots): `#anatomy?snapshot=<id>` показывает срез снэпшота.
- 🔬 Research ↔ 🧬 Anatomy: из Snapshots можно перейти обратно в Anatomy.

## Бэкенд — роутеры (`backend/api/`)

Роутеры регистрируются в `backend/main.py` через `_register_routers()`. Структура отличается от старой `backend/app/routers/` (больше не используется):

| Префикс | Файл | Назначение |
|---------|------|-----------|
| `/api/v1` | `frontend_routes.py`, `document_routes.py`, `routes.py` | Фронт-API, документы |
| `/api/v1/user` | `user_routes.py` | Пользователи + **`/keys`** (API-ключи) |
| `/api/v1/dialogs` | `dialog_routes.py` | История диалогов |
| `/api/v1/xray` | `xray_routes.py` | X-Ray наблюдаемость |
| `/api/v1/metrics` | `metrics_routes.py` | Метрики pipeline/системы |
| `/api/v1/memory` | `memory_routes.py` | Memory-дашборд |
| `/api/v1/knowledge` | `knowledge_routes.py` | Граф знаний |
| `/api/v1/feedback` | `feedback_routes.py` | Обратная связь |
| `/api/v1/healer` | `healer_routes.py` | HEALER |
| `/api/v1/experience` | `experience_routes.py` | Опыт |
| `/api/v1/admin/persona` | `persona_routes.py` | Persona (admin) |
| `/api/v1/impulse` | `impulse_routes.py` | Impulse Core |
| `/api/v1/admin` | `admin_routes.py` | Admin |
| `/api/v1/sentry` | `sentry_routes.py` | Sentry-совместимый ingest |
| `/api/v1/experiments` | `experiments_routes.py` | Research Platform (runs/compare/evals) |
| `/api/v1/decisions` | `decisions_routes.py` | Decision Log |
| `/api/v1/anatomy` | `anatomy_routes.py` | 🧬 Живая анатомия |
| `/api/v1/learning` | `learning_routes.py` | Обучение |
| `/api/v1/debug` | `debug_routes.py` | Только при `DEBUG=true` |

## Память

### 6 типов памяти

| Тип | Хранилище | Описание |
|-----|-----------|----------|
| **RAG** | PostgreSQL/pgvector | Семантическая память диалогов |
| **Episodic** | SQLite | Эпизоды с временными метками |
| **Semantic** (включая Facts) | SQLite | Общие знания, концепции, факты |
| **Roots** | JSON | Фундаментальные принципы |
| **Persona** | SQLite | Личность с 8 чертами |
| **Hygiene** | — | Автоматическая очистка |

### RAG v3.0

- Классификация тем (7 категорий)
- Извлечение сущностей (6 типов)
- Извлечение связей
- Гибридный поиск
- LLM-суммаризация

## Эмоции (PAD+)

6 измерений:

| Измерение | Диапазон | Описание |
|-----------|----------|----------|
| Удовольствие | -1.0 ... +1.0 | Положительные/отрицательные чувства |
| Возбуждение | -1.0 ... +1.0 | Энергичность |
| Доминирование | -1.0 ... +1.0 | Контроль ситуации |
| Любопытство | 0.0 ... 1.0 | Интерес к новому |
| Уверенность | 0.0 ... 1.0 | Уверенность в ответах |
| Социальная связь | -1.0 ... +1.0 | Связь с пользователем |

**Затухание:** 0.001/сек, возврат к нейтральному состоянию.

## Провайдеры LLM

Через **ProviderManager** + прямой SDK:

| Провайдер | Аутентификация | Бесплатно |
|-----------|---------------|-----------|
| GigaChat | OAuth | ✅ |
| Groq | API Key | ✅ |
| OpenAI | API Key | ❌ |
| Google Gemini | API Key | ✅ |
| Anthropic Claude | API Key | ❌ |
| OpenRouter | API Key | ✅ (частично) |

## Безопасность

- **Safety Layer** — защита от инъекций
- **Rate Limiter** — ограничение запросов
- **Anti-Loop Guard** — защита от зацикливаний
- **Encryption** — шифрование API ключей (Fernet)

## Автономность

- **Планировщик** — самостоятельные вопросы
- **Иерархический планировщик** — Goals → Tasks → Actions
- **Dreams** — обработка памяти в покое
- **Саморефлексия** — анализ качества ответов
- **Консолидация** — перенос эпизодов в семантическую память
- **ControlTick** — фоновый автономный цикл (каждые 60с):
  - **Self-Evaluation** — оценка своей производительности (health score, response time, errors)
  - **Feedback Request** — запрос фидбека у пользователя (nudge после N диалогов)
  - **Meta-Learner** — анализ стратегий генерации по 3 критериям (успешность, эффективность, качество), рекомендация смены стратегии
  - Обновление Dashboard-метрик
- **ActiveLearning (EvaluationPhase)** — самооценка каждого ответа по 4 критериям: точность, полнота, полезность, безопасность. Результаты сохраняются в опыт и влияют на эмоции.
- **Meta-Learner** — анализирует паттерны стратегий, кластеризует по успешности, выдаёт рекомендацию: «сменить стратегию на X» при падении эффективности.

## База данных

### Supabase (PostgreSQL)

| Таблица | Описание |
|---------|----------|
| `user_api_keys` | API ключи пользователей (зашифрованы) |
| `users` | Пользователи (через Supabase Auth) |

### SQLite (локальные данные)

| Файл | Данные |
|------|--------|
| `data/` | Данные (SQLite, JSON) |
| `data/*.json` | Состояния (эмоции, persona, roots) |

## Мониторинг

| Эндпоинт | Описание |
|----------|----------|
| `GET /api/v1/health` | Проверка здоровья (core runtime + БД) |
| `GET /api/v1/mind-state` | Полное состояние (PAD, persona, stats) |
| `GET /api/v1/xray/brain/status` | Состояние X-Ray (system_state + meta_learner + reflection) |
| `GET /api/v1/metrics/pipeline` | Счётчики/гистограммы pipeline |
| `GET /api/v1/metrics/system` | CPU, память, соединения, стоимость |
| `GET /api/v1/anatomy` | Дерево живой анатомии (статус всех модулей) |
| `WS /ws` (или `/ws/{client_id}`) | Real-time события |

## Запуск

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8007

# Frontend
cd frontend && npm run dev
```

Откройте http://localhost:5174
