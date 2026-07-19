# 📚 PAD+ AI — API Specification v4.0

*PAD+ = Pleasure, Arousal, Dominance + Curiosity, Confidence, Social Connection*

> ⚠️ **Актуальность:** документ синхронизирован с реальными роутерами в `backend/api/` (июль 2026). Старые эндпоинты `/rag/*`, `/episodic/*`, `/semantic/*`, `/gigachat/*`, `/dreams/*`, `/autonomy/*`, `/plans/*` **удалены** — вместо них используйте `/api/v1/memory`, `/api/v1/xray`, `/api/v1/anatomy`, `/api/v1/experiments` и др.

## Base URL

```
http://localhost:8007/api/v1
```

Production: `https://pad-plus-ai.onrender.com/api/v1`

## Содержание

1. [Auth](#auth)
2. [Providers & Keys](#providers--keys)
3. [Chat & Mind State](#chat--mind-state)
4. [🧬 Living Anatomy](#-living-anatomy)
5. [Research Platform (Experiments)](#research-platform-experiments)
6. [Decision Log](#decision-log)
7. [X-Ray](#x-ray)
8. [Metrics](#metrics)
9. [Memory](#memory)
10. [Knowledge Graph](#knowledge-graph)
11. [Impulse Core](#impulse-core)
12. [HEALER](#healer)
13. [Experience](#experience)
14. [Learning](#learning)
15. [Documents & Collections](#documents--collections)
16. [Dialogs](#dialogs)
17. [Feedback](#feedback)
18. [User & Settings](#user--settings)
19. [Admin](#admin)
20. [Sentry](#sentry)
21. [Debug](#debug)
22. [WebSocket](#websocket)

---

## Auth

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/auth/register` | Регистрация (Supabase) |
| POST | `/api/v1/auth/login` | Вход |
| GET | `/api/v1/auth/me` | Текущий пользователь |
| POST | `/api/v1/auth/refresh` | Обновление токена |

---

## Providers & Keys

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/providers` | Список доступных провайдеров |
| GET | `/api/v1/providers/status` | Статус провайдеров |
| GET | `/api/v1/providers/{provider_id}/models` | Модели провайдера |
| GET | `/api/v1/keys` | Список ключей пользователя (пагинация) |
| POST | `/api/v1/keys` | Добавить ключ |
| PATCH | `/api/v1/keys/{key_id}` | Обновить ключ (модель, имя, is_default) |
| DELETE | `/api/v1/keys/{key_id}` | Удалить ключ |
| POST | `/api/v1/keys/{key_id}/set-default` | Сделать ключ основным |
| POST | `/api/v1/keys/{key_id}/test` | Протестировать ключ |
| GET | `/api/v1/keys/status/batch` | Статус всех ключей (с кэшем) |
| POST | `/api/v1/keys/status/{key_id}/refresh` | Обновить статус ключа |

> ℹ️ Ранее существовавший `legacy_routes.py` (заглушки 503 для `/providers` и `/keys`) **удалён** — он был мёртвым кодом и не регистрировался в `main.py`.

---

## Chat & Mind State

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/chat` | Основной чат (авто-выбор провайдера/модели) |
| POST | `/api/v1/chat/stream` | Потоковый чат (SSE) |
| GET | `/api/v1/mind-state` | Полное состояние системы (PAD, persona, stats) |
| GET | `/api/v1/system/full-status` | Полный статус всех систем |
| GET | `/api/v1/events/recent` | История недавних событий |
| GET | `/api/v1/metrics/activity` | Метрики активности |
| GET | `/api/v1/models` | Список доступных моделей |
| GET | `/api/v1/settings` | Настройки пользователя |
| PATCH | `/api/v1/settings` | Обновить настройки |
| GET | `/api/v1/health` | Health check |

**Пример — основной чат:**
```bash
curl -X POST http://localhost:8007/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет!", "session_id": "sess-123"}'
```

---

## 🧬 Living Anatomy

Визуализация когнитивной архитектуры в реальном времени. Источник: `backend/core/anatomy.py`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/anatomy` | Полное дерево живой анатомии (brain → 11 модулей → подмодули) |
| GET | `/api/v1/anatomy/{module_id}` | Деталь конкретного модуля (component + decision_count) |

**Ответ `GET /api/v1/anatomy`:**
```json
{
  "brain": {
    "label": "Brain",
    "status": "active",
    "metrics": { "modules": 11, "strategy": "reasoning" },
    "children": {
      "memory": {
        "label": "Memory", "status": "active",
        "metrics": { "modules": 5, "items": 1234 },
        "children": {
          "episodic":  { "label": "Episodic", "status": "active", "metrics": { "episodes": 500 } },
          "semantic":  { "label": "Semantic", "status": "active", "metrics": { "knowledge": 300, "avg_confidence": 0.8 } },
          "rag":       { "label": "RAG", "status": "active", "metrics": { "dialogs": 200 } },
          "persona":   { "label": "Persona", "status": "active", "metrics": { "traits": 8, "interactions": 50 } },
          "roots":     { "label": "Roots", "status": "active", "metrics": { "roots": 12 } }
        }
      },
      "reasoning": { "label": "Reasoning", "status": "active", "metrics": { "strategy": "reasoning", "success_rate": 0.9, "decisions": 42 } },
      "identity":  { "label": "Identity", "status": "active", "metrics": {} },
      "emotion":   { "label": "Emotion", "status": "active", "metrics": { "pleasure": 0.1, "arousal": 0.2, "dominance": 0.0, "curiosity": 0.7, "confidence": 0.6 } },
      "reflection":{ "label": "Reflection", "status": "active", "metrics": { "count": 10, "adjustments": 3 } },
      "dreams":    { "label": "Dreams", "status": "active", "metrics": { "total_dreams": 5, "consolidated": 2, "is_dreaming": false } },
      "truth":     { "label": "Truth", "status": "active", "metrics": { "claims": 100, "avg_confidence": 0.85 } },
      "safety":    { "label": "Safety", "status": "active", "metrics": { "autonomy": true, "strict_mode": false, "requests_1m": 0 } },
      "healer":    { "label": "Healer", "status": "active", "metrics": { "mode": "monitor", "remediations": 1, "cycles": 3 } },
      "research":  { "label": "Research", "status": "active", "metrics": { "decisions": 42, "components": 5 } },
      "xray":      { "label": "X-Ray", "status": "active", "metrics": { "traces": 7 } }
    }
  },
  "timestamp": "2026-07-19T12:00:00"
}
```

**Модули первого уровня:** `memory`, `reasoning`, `identity`, `emotion`, `reflection`, `dreams`, `truth`, `safety`, `healer`, `research`, `xray`.

**Кросс-ссылка Decision Log** (поле `component` в детали модуля):
`reflection`→reflection, `dreams`→reflection, `healer`→healing, `reasoning`→strategy_selector, `research`→provider_selector.

---

## Research Platform (Experiments)

Источник: `backend/api/experiments_routes.py`. Префикс `/api/v1/experiments`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/experiments/runs` | Список прогонов экспериментов |
| GET | `/api/v1/experiments/runs/{name}` | Детали прогона (raw + config + report) |
| GET | `/api/v1/experiments/runs/{name}/report` | Отчёт прогона (markdown) |
| GET | `/api/v1/experiments/compare?baseline=X&treatment=Y` | Сравнение двух прогонов |
| GET | `/api/v1/experiments/traces` | Список X-Ray трасс |
| GET | `/api/v1/experiments/traces/{trace_id}` | Детали трассы |
| GET | `/api/v1/experiments/pipeline/registry` | Реестр фаз pipeline |
| GET | `/api/v1/experiments/evals?limit=N` | Оценки качества (средние, по стратегиям/провайдерам) |
| POST | `/api/v1/experiments/snapshot` | Создать снэпшот |
| GET | `/api/v1/experiments/snapshots` | Список снэпшотов |
| GET | `/api/v1/experiments/snapshots/{snapshot_id}` | Детали снэпшота |
| POST | `/api/v1/experiments/snapshots/{snapshot_id}/link-to-run/{run_name}` | Привязать снэпшот к прогону |
| GET | `/api/v1/experiments/snapshots/{snapshot_id}/decisions` | Решения Decision Log после снэпшота |

---

## Decision Log

Источник: `backend/api/decisions_routes.py`. Префикс `/api/v1/decisions`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/decisions?component=&type=&session=&trace=&since=` | Список решений (фильтры) |
| GET | `/api/v1/decisions/stats` | Статистика решений |
| GET | `/api/v1/decisions/{decision_id}` | Детали решения |
| GET | `/api/v1/decisions/session/{session_id}` | Решения сессии |

---

## X-Ray

Источник: `backend/api/xray_routes.py`. Префикс `/api/v1/xray`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/xray/brain/status` | Статус X-Ray Brain (system_state + meta_learner + reflection) |
| GET | `/api/v1/xray/brain/strategies` | Статистика по стратегиям Brain |
| POST | `/api/v1/xray/brain/strategy` | Принудительно установить стратегию |
| GET | `/api/v1/xray/stats` | Общая статистика X-Ray |
| GET | `/api/v1/xray/active` | Активные сессии трассировки |
| GET | `/api/v1/xray/recent` | Последние завершённые трассы |
| GET | `/api/v1/xray/sessions` | Список сессий |
| GET | `/api/v1/xray/sessions/{session_id}` | Детали сессии |
| GET | `/api/v1/xray/sessions/{session_id}/export` | Экспорт сессии (json/csv) |
| DELETE | `/api/v1/xray/sessions/{session_id}` | Удаление сессии |
| GET | `/api/v1/xray/pipeline/stages` | Стадии pipeline для визуализации |
| POST | `/api/v1/xray/trace/start` | Начало сессии трассировки |
| POST | `/api/v1/xray/trace/complete` | Завершение сессии трассировки |
| WS | `/api/v1/xray/ws` | WebSocket real-time событий |

---

## Metrics

Источник: `backend/api/metrics_routes.py`. Префикс `/api/v1/metrics`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/metrics/pipeline` | Статистика pipeline (counters, histograms, timeseries) |
| GET | `/api/v1/metrics/system` | Системные метрики (CPU, память, соединения, стоимость) |
| GET | `/api/v1/metrics/dashboard` | Метрики для дашборда (JSON) |
| GET | `/api/v1/metrics/summary` | Краткая сводка |
| GET | `/api/v1/metrics/memory` | Метрики памяти (Memory Manager) |
| GET | `/api/v1/metrics/db-circuit-breaker` | Статус DB Circuit Breaker |
| POST | `/api/v1/metrics/reset` | Сброс всех метрик |

---

## Memory

Источник: `backend/api/memory_routes.py`. Префикс `/api/v1/memory`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/memory/dashboard` | Агрегированная статистика всех систем памяти |
| POST | `/api/v1/memory/consolidation/trigger` | Ручной запуск консолидации |

> Детальные операции по эпизодам/семантике доступны через MemoryManager (`backend/memory/`) и агрегируются в `dashboard`.

---

## Knowledge Graph

Источник: `backend/api/knowledge_routes.py`. Префикс `/api/v1/knowledge`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/knowledge/graph` | Полный граф для визуализации |
| GET | `/api/v1/knowledge/stats` | Статистика графа |
| GET | `/api/v1/knowledge/search` | Поиск концепций |
| GET | `/api/v1/knowledge/related/{concept_id}` | Связанные концепции |
| GET | `/api/v1/knowledge/semantic-search` | Семантический поиск (vector) |
| POST | `/api/v1/knowledge/concepts` | Добавить концепцию |
| POST | `/api/v1/knowledge/concepts/batch` | Пакетное добавление |
| POST | `/api/v1/knowledge/relations` | Добавить связь |
| PATCH | `/api/v1/knowledge/relations` | Обновить/создать связь |
| POST | `/api/v1/knowledge/extract` | Извлечь концепции/связи из текста |
| POST | `/api/v1/knowledge/recompute-embeddings` | Перегенерация эмбеддингов |
| POST | `/api/v1/knowledge/concepts/{concept_id}/merge` | Объединить концепции |
| DELETE | `/api/v1/knowledge/concepts/{concept_id}` | Удалить концепцию |

---

## Impulse Core

Источник: `backend/api/impulse_routes.py`. Префикс `/api/v1/impulse`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/impulse` | Текущее состояние импульсного ядра |
| PUT | `/api/v1/impulse` | Установить веса импульсов |
| PUT | `/api/v1/impulse/question` | Установить импульс по строке вопроса |
| POST | `/api/v1/impulse/push` | Сохранить состояние в стек |
| POST | `/api/v1/impulse/pop` | Восстановить из стека |
| GET | `/api/v1/impulse/labels` | Все метки импульсов |
| POST | `/api/v1/impulse/preset` | Установить пресет (strict/balanced/creative) |

---

## HEALER

Источник: `backend/api/healer_routes.py`. Префикс `/api/v1/healer`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/healer/status` | Статус HealerListener |
| GET | `/api/v1/healer/mode` | Текущий режим (monitor/suggest/auto) |
| POST | `/api/v1/healer/mode` | Установить режим |
| POST | `/api/v1/healer/diagnose` | Ручная диагностика |
| GET | `/api/v1/healer/reports` | Последние отчёты диагностики |
| GET | `/api/v1/healer/remediation` | История remediate-действий |
| GET | `/api/v1/healer/tone` | Статус ToneEngine |
| POST | `/api/v1/healer/tone` | Вкл/выкл ToneEngine |
| GET | `/api/v1/healer/bridge/status` | Статус HealerBridge |
| POST | `/api/v1/healer/bridge/diagnose` | Диагностика HEALER |
| POST | `/api/v1/healer/bridge/cycle` | Полный healing cycle |
| GET | `/api/v1/healer/bridge/orchestrator` | Статус Orchestrator |
| GET | `/api/v1/healer/bridge/reflection/latest` | Последняя рефлексия |
| GET | `/api/v1/healer/bridge/changes` | Список изменений HEALER |
| POST | `/api/v1/healer/bridge/rollback/{patch_id}` | Откат патча |
| GET/POST/DELETE/PUT | `/api/v1/healer/bridge/auto-cycle` | Управление автоциклами |

---

## Experience

Источник: `backend/api/experience_routes.py`. Префикс `/api/v1/admin/experiences`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/admin/experiences` | Список записей опыта (фильтр/пагинация) |
| GET | `/api/v1/admin/experiences/stats` | Сводка по опыту |

---

## Learning

Источник: `backend/api/learning_routes.py`. Префикс `/api/v1/learning`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/learning/stats` | Статистика обучения |
| GET | `/api/v1/learning/evaluation/recent` | Последние оценки |
| GET | `/api/v1/learning/experience/stats` | Статистика experience-learner |
| GET | `/api/v1/learning/experience/recent` | Последние опыты |
| GET | `/api/v1/learning/active/policy` | Состояние active-policy |
| POST | `/api/v1/learning/active/reset` | Сброс active-policy |

---

## Documents & Collections

Источник: `backend/api/document_routes.py`. Префикс `/api/v1`.

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/documents/upload` | Загрузка документа |
| GET | `/api/v1/documents` | Список документов |
| GET | `/api/v1/documents/stats` | Статистика документов |
| GET | `/api/v1/documents/{document_id}` | Детали документа |
| PATCH | `/api/v1/documents/{document_id}` | Обновить документ |
| DELETE | `/api/v1/documents/{document_id}` | Удалить документ |
| GET | `/api/v1/documents/trash` | Корзина |
| POST | `/api/v1/documents/{document_id}/restore` | Восстановить из корзины |
| DELETE | `/api/v1/documents/trash/clear` | Очистить корзину |
| GET | `/api/v1/documents/search` | RAG-поиск |
| GET | `/api/v1/documents/settings` | Настройки обработки |
| POST | `/api/v1/documents/from-url` | Загрузка из URL |
| GET | `/api/v1/collections` | Список коллекций |
| POST | `/api/v1/collections` | Создать коллекцию |
| DELETE | `/api/v1/collections/{collection_id}` | Удалить коллекцию |

---

## Dialogs

Источник: `backend/api/dialog_routes.py`. Префикс `/api/v1/dialogs`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/dialogs` | Список диалогов (пагинация, фильтр избранного) |
| GET | `/api/v1/dialogs/stats` | Статистика диалогов |
| GET | `/api/v1/dialogs/search` | Поиск по диалогам |
| GET | `/api/v1/dialogs/{dialog_id}` | Детали диалога с сообщениями |
| DELETE | `/api/v1/dialogs/{dialog_id}` | Удалить диалог |
| DELETE | `/api/v1/dialogs` | Очистить всю историю |
| POST | `/api/v1/dialogs/{dialog_id}/favorite` | Вкл/выкл избранное |
| POST | `/api/v1/dialogs/{dialog_id}/export` | Экспорт (json/txt) |

---

## Feedback

Источник: `backend/api/feedback_routes.py`. Префикс `/api/v1/feedback`.

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/feedback` | Отправить оценку ответа |
| GET | `/api/v1/feedback/stats` | Статистика обратной связи |

---

## User & Settings

Источник: `backend/api/user_routes.py`. Префикс `/api/v1/user`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/user/profile` | Профиль пользователя |
| PATCH | `/api/v1/user/profile` | Обновить профиль |
| PATCH | `/api/v1/user/password` | Смена пароля |
| POST | `/api/v1/user/avatar` | Загрузить аватар |
| DELETE | `/api/v1/user/avatar` | Удалить аватар |
| GET | `/api/v1/user/persona` | Настройки persona |
| PATCH | `/api/v1/user/persona` | Обновить настройки persona |
| GET | `/api/v1/user/notifications` | Настройки уведомлений |
| PATCH | `/api/v1/user/notifications` | Обновить уведомления |
| GET | `/api/v1/user/appearance` | Настройки внешнего вида |
| PATCH | `/api/v1/user/appearance` | Обновить внешний вид |
| GET | `/api/v1/user/settings` | Все настройки пользователя |

---

## Admin

Источник: `backend/api/admin_routes.py`, `backend/api/persona_routes.py`. Префикс `/api/v1/admin`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/admin/emotion` | Статистика эмоций (learner + PAD) |
| GET | `/api/v1/admin/sync` | Статус cross-memory sync |
| POST | `/api/v1/admin/sync/trigger` | Запуск синхронизации памяти |
| GET | `/api/v1/admin/health` | Когнитивное здоровье системы |
| GET | `/api/v1/admin/persona/deltas` | Дельты эволюции эмоций/импульсов/персоны |

---

## Sentry

Источник: `backend/api/sentry_routes.py`. Префикс `/api/v1/sentry`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/sentry/webhook` | Верификация webhook Sentry |
| POST | `/api/v1/sentry/webhook` | Обработка webhook Sentry (запуск HEALER) |

---

## Debug

Источник: `backend/api/debug_routes.py`. Префикс `/api/v1/debug` (только при `DEBUG=true`).

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/debug/gigachat` | Диагностика GigaChat (env/URL/DNS/TCP) |
| GET | `/api/v1/debug/key-access` | Диагностика доступа к API-ключам |

---

## WebSocket

| Путь | Описание |
|------|----------|
| `WS /api/v1/xray/ws` | Real-time события X-Ray (трассы, мысли, статус) |
| `WS /ws` или `WS /ws/{client_id}` | Общие real-time события системы |

---

## Прочее

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/info` | Корневой info-эндпоинт (версия 4.0) |
