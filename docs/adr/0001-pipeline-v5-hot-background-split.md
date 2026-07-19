# ADR-0001: Pipeline v5.0 — Hot/Background Split

**Дата:** 2026-07-17
**Статус:** Принято
**Автор:** PAD+ AI Core Team

## Контекст

Pipeline v4.0 выполнял все фазы последовательно (24 фазы). Это приводило к
задержке ответа — фазы analytics (health, metrics, dreams) выполнялись
до отправки ответа пользователю.

## Решение

Разделить фазы на два пути:
- **Sync path (hot):** фазы, влияющие на ответ (generate, truth_loop,
  response_guard) — выполняются `await`, пользователь ждёт
- **Background path:** фазы аналитики/записи (consolidation, dreams,
  metrics) — fire-and-forget через `asyncio.create_task()`

```python
_BACKGROUND_PHASES: Set[str] = {
    "consolidation", "procedure_success",
    "persona_evolution", "health",
    "reflection", "dreams", "metrics",
}
```

## Последствия

- Время ответа пользователю сократилось на ~30-50%
- Background-фазы могут не успеть выполниться при рестарте сервера
- Lock для consolidation заменён на counter + threshold (гонка невозможна)

## Альтернативы

- **Actor model:** избыточно для текущей нагрузки
- **Отдельный worker:** требует RabbitMQ/Redis — преждевременно

## Совместимость

API не изменился. `PipelineResult` возвращается сразу, background-фазы
не влияют на ответ.
