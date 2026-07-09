from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from core.events import Event, Events, get_events


@pytest.fixture(autouse=True)
def reset_events():
    import core.events as mod
    mod._events = None
    yield
    mod._events = None


class TestEvent:
    def test_subscribe_and_publish_sync(self):
        event = Event("test")
        results = []

        def handler(data):
            results.append(data)

        event.subscribe(handler)
        import asyncio
        asyncio.run(event.publish({"key": "val"}))

        assert len(results) == 1
        assert results[0]["key"] == "val"

    @pytest.mark.asyncio
    async def test_subscribe_and_publish_async(self):
        event = Event("test")
        results = []

        async def handler(data):
            results.append(data)

        event.subscribe(handler)
        await event.publish({"key": "val"})

        assert len(results) == 1

    def test_unsubscribe(self):
        event = Event("test")
        results = []

        def handler(data):
            results.append(data)

        event.subscribe(handler)
        event.unsubscribe(handler)
        import asyncio
        asyncio.run(event.publish({"key": "val"}))

        assert len(results) == 0

    def test_multiple_subscribers(self):
        event = Event("test")
        results1 = []
        results2 = []

        def h1(data):
            results1.append(data)

        def h2(data):
            results2.append(data)

        event.subscribe(h1)
        event.subscribe(h2)
        import asyncio
        count = asyncio.run(event.publish({"key": "val"}))

        assert count == 2
        assert len(results1) == 1
        assert len(results2) == 1

    def test_handler_exception_does_not_block_others(self):
        event = Event("test")
        results = []

        def failing(data):
            raise ValueError("fail")

        def ok(data):
            results.append(data)

        event.subscribe(failing)
        event.subscribe(ok)
        import asyncio
        count = asyncio.run(event.publish({"key": "val"}))

        assert count == 2  # failing counted too (was attempted)
        assert len(results) == 1

    def test_subscriber_count(self):
        event = Event("test")

        def h1(data):
            pass

        async def h2(data):
            pass

        assert event.subscriber_count == 0
        event.subscribe(h1)
        assert event.subscriber_count == 1
        event.subscribe(h2)
        assert event.subscriber_count == 2
        event.unsubscribe(h1)
        assert event.subscriber_count == 1


class TestEvents:
    def test_singleton(self):
        a = get_events()
        b = get_events()
        assert a is b

    def test_get_stats(self):
        events = get_events()
        stats = events.get_stats()
        assert "events_published" in stats
        assert "last_events" in stats
        assert "subscribers" in stats
        assert stats["events_published"] == 0

    @pytest.mark.asyncio
    async def test_event_xray_meta(self):
        events = get_events()
        await events.dialog_completed.publish({"test": True})
        stats = events.get_stats()
        assert stats["events_published"] == 1
        assert stats["last_events"][0]["event_name"] == "dialog_completed"
        assert stats["last_events"][0]["subscriber_count"] == 0

    @pytest.mark.asyncio
    async def test_dialog_completed_event_in_pipeline(self):
        with patch("core.events.get_events") as mock_get_events:
            mock_events = MagicMock()
            mock_events.dialog_completed = AsyncMock()
            mock_get_events.return_value = mock_events

            from core.pipeline import get_pipeline
            pipeline = get_pipeline()
            result = await pipeline.execute("привет", context={"user_id": "test"}, api_key="sk-test")

            mock_events.dialog_completed.publish.assert_called_once()
            call_data = mock_events.dialog_completed.publish.call_args[0][0]
            assert call_data["user_message"] == "привет"
            assert "strategy" in call_data
            assert "success" in call_data

    def test_events_registry_has_all_events(self):
        events = get_events()
        assert hasattr(events, "dialog_completed")
        assert hasattr(events, "strategy_changed")
        assert hasattr(events, "experience_captured")
