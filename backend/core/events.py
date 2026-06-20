import asyncio
import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

logger = logging.getLogger("padplus.events")

T = TypeVar("T")


@dataclass
class EventMeta:
    event_name: str
    duration_ms: float
    subscriber_count: int
    timestamp: float


class Event(Generic[T]):
    def __init__(self, name: str):
        self._name = name
        self._sync_handlers: List[Callable[[T], None]] = []
        self._async_handlers: List[Callable[[T], Any]] = []

    def subscribe(self, handler: Callable) -> None:
        if asyncio.iscoroutinefunction(handler):
            self._async_handlers.append(handler)
        else:
            self._sync_handlers.append(handler)

    def unsubscribe(self, handler: Callable) -> None:
        self._sync_handlers = [h for h in self._sync_handlers if h is not handler]
        self._async_handlers = [h for h in self._async_handlers if h is not handler]

    @property
    def subscriber_count(self) -> int:
        return len(self._sync_handlers) + len(self._async_handlers)

    async def publish(self, data: T) -> int:
        import time
        start = time.time()
        count = 0
        for handler in self._sync_handlers:
            count += 1
            try:
                handler(data)
            except Exception as e:
                logger.warning("Event '%s' sync handler error: %s", self._name, e)
        for handler in self._async_handlers:
            count += 1
            try:
                await handler(data)
            except Exception as e:
                logger.warning("Event '%s' async handler error: %s", self._name, e)
        _record_event_meta(EventMeta(
            event_name=self._name,
            duration_ms=(time.time() - start) * 1000,
            subscriber_count=count,
            timestamp=start,
        ))
        return count


class Events:
    def __init__(self):
        self.dialog_completed: Event[Dict[str, Any]] = Event("dialog_completed")
        self.strategy_changed: Event[Dict[str, Any]] = Event("strategy_changed")
        self.experience_captured: Event[Dict[str, Any]] = Event("experience_captured")
        self._all_events = {
            "dialog_completed": self.dialog_completed,
            "strategy_changed": self.strategy_changed,
            "experience_captured": self.experience_captured,
        }
        self._event_meta: List[EventMeta] = []

    def get_stats(self) -> Dict[str, Any]:
        return {
            "events_published": len(self._event_meta),
            "last_events": [m.__dict__ for m in self._event_meta[-10:]],
            "subscribers": {
                name: event.subscriber_count
                for name, event in self._all_events.items()
            },
        }


_events: Optional[Events] = None


def get_events() -> Events:
    global _events
    if _events is None:
        _events = Events()
    return _events


def _record_event_meta(meta: EventMeta) -> None:
    events = get_events()
    events._event_meta.append(meta)
    if len(events._event_meta) > 100:
        events._event_meta = events._event_meta[-100:]
