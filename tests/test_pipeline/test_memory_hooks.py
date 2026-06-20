from unittest.mock import MagicMock, patch, call

import pytest

from core.pipeline.memory_hooks import MemoryHookManager, get_memory_hooks


@pytest.fixture(autouse=True)
def reset_hooks():
    mgr = get_memory_hooks()
    mgr.reset()
    yield
    mgr.reset()


class TestMemoryHookManager:
    def test_register_and_execute(self):
        mgr = MemoryHookManager()
        calls = []

        def handler(ctx):
            calls.append(ctx["value"])

        mgr.register("before_pipeline", handler)
        mgr.execute("before_pipeline", {"value": 42})
        assert calls == [42]

    def test_unknown_hook_point(self):
        mgr = MemoryHookManager()
        mgr.register("invalid", lambda ctx: None)  # should not raise

    def test_handler_exception_silent(self):
        mgr = MemoryHookManager()

        def failing(ctx):
            raise ValueError("boom")

        mgr.register("before_pipeline", failing)
        mgr.execute("before_pipeline", {})  # should not raise

    def test_multiple_handlers(self):
        mgr = MemoryHookManager()
        calls = []

        def h1(ctx):
            calls.append("h1")

        def h2(ctx):
            calls.append("h2")

        mgr.register("after_phase", h1)
        mgr.register("after_phase", h2)
        mgr.execute("after_phase", {})
        assert calls == ["h1", "h2"]

    def test_reset_clears(self):
        mgr = MemoryHookManager()
        mgr.register("before_pipeline", lambda ctx: None)
        mgr.reset()
        assert len(mgr._hooks["before_pipeline"]) == 0

    def test_singleton(self):
        a = get_memory_hooks()
        b = get_memory_hooks()
        assert a is b


class TestDefaultHooks:
    def test_register_default_hooks(self):
        mgr = get_memory_hooks()
        from core.pipeline.memory_hooks import register_default_hooks
        register_default_hooks()

        assert len(mgr._hooks["before_pipeline"]) == 1
        assert len(mgr._hooks["after_phase"]) == 1
        assert len(mgr._hooks["before_response"]) == 1
        assert len(mgr._hooks["after_process"]) == 1

    def test_before_pipeline_loads_persona(self):
        with patch("memory.get_user_persona_manager") as mock_pm, \
             patch("core.pipeline.memory_hooks.get_memory_hooks") as mock_get:
            mock_mgr = MagicMock()
            mock_get.return_value = mock_mgr
            mock_persona = MagicMock()
            mock_persona.style_preferences = {"verbosity": 0.7}
            mock_pm.return_value.get_persona.return_value = mock_persona

            from core.pipeline.memory_hooks import _before_pipeline_impl
            ctx = {"user_id": "user1"}
            _before_pipeline_impl(ctx)

            assert ctx["user_persona"] is mock_persona
            assert ctx["style_preferences"] == {"verbosity": 0.7}

    def test_before_pipeline_no_user_id(self):
        from core.pipeline.memory_hooks import _before_pipeline_impl
        ctx = {}
        _before_pipeline_impl(ctx)
        # should not raise

    def test_after_process_saves_persona(self):
        with patch("memory.get_user_persona_manager") as mock_pm, \
             patch("memory.get_rag") as mock_rag:
            mock_persona = MagicMock()
            mock_pm.return_value.get_persona.return_value = mock_persona
            mock_rag_instance = MagicMock()
            mock_rag.return_value = mock_rag_instance

            from core.pipeline.memory_hooks import _after_process_impl
            ctx = {"user_id": "u1", "user_message": "hi", "_generated_response": "hello"}
            _after_process_impl(ctx)

            mock_pm.return_value.save_persona.assert_called_once()
            mock_rag_instance.add_dialog.assert_called_once_with("hi", "hello", user_id="u1")

    def test_after_process_no_response(self):
        from core.pipeline.memory_hooks import _after_process_impl
        ctx = {"user_id": "u1", "user_message": "hi"}
        _after_process_impl(ctx)
        # should not call anything without response

    def test_before_response_updates_topics(self):
        with patch("memory.rag_postgres.classify_topic") as mock_classify:
            mock_classify.return_value = ("tech", 0.8)
            mock_persona = MagicMock()
            mock_persona.frequent_topics = {}
            mock_persona.total_interactions = 0

            from core.pipeline.memory_hooks import _before_response_impl
            ctx = {"user_id": "u1", "user_persona": mock_persona, "user_message": "how to code?", "_generated_response": "here's how"}
            _before_response_impl(ctx)

            assert mock_persona.frequent_topics["tech"] == 1
            assert mock_persona.total_interactions == 1
