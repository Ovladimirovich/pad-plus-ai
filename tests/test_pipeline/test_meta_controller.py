from unittest.mock import patch

import pytest

from core.meta_controller import (
    CognitiveState,
    MetaController,
    get_meta_controller,
    reset_meta_controller,
)


@pytest.fixture(autouse=True)
def reset():
    reset_meta_controller()


class TestMetaController:
    def test_singleton(self):
        a = get_meta_controller()
        b = get_meta_controller()
        assert a is b

    def test_initial_state(self):
        mc = get_meta_controller()
        assert mc.get_state() == CognitiveState.IDLE

    def test_set_state(self):
        mc = get_meta_controller()
        mc.set_state(CognitiveState.PROCESSING)
        assert mc.get_state() == CognitiveState.PROCESSING

    def test_adapt_collects_snapshot(self):
        mc = get_meta_controller()
        mc.adapt({
            "strategy_success": True,
            "interaction_type": "praise",
            "significance": 0.5,
            "emotion": {"pleasure": 0.3},
            "impulse_primary": "understand",
        })
        assert len(mc.get_snapshots()) == 1

    @patch("core.xray.meta_learner.get_meta_learner")
    def test_adapt_triggers_reflection_on_low_success(self, mock_get_ml):
        mock_meta = mock_get_ml.return_value
        mock_meta.get_all_stats.return_value = {
            "simple": {"success_rate": 0.3},
        }

        mc = get_meta_controller()
        mc.adapt({
            "strategy_success": False,
            "interaction_type": "criticism",
            "significance": 0.3,
        })
        assert mc.get_state() == CognitiveState.REFLECTING

    def test_adapt_triggers_reflection_on_high_significance(self):
        mc = get_meta_controller()
        mc.adapt({
            "strategy_success": True,
            "interaction_type": "contradiction",
            "significance": 0.9,
        })
        assert mc.get_state() == CognitiveState.REFLECTING

    def test_adapt_triggers_reflection_after_10_dialogs(self):
        mc = get_meta_controller()
        for _ in range(9):
            mc.adapt({
                "strategy_success": True,
                "interaction_type": "new_knowledge",
                "significance": 0.1,
            })
        assert mc.get_state() == CognitiveState.IDLE
        mc.adapt({
            "strategy_success": True,
            "interaction_type": "new_knowledge",
            "significance": 0.1,
        })
        assert mc.get_state() == CognitiveState.REFLECTING

    def test_returns_to_idle_after_reflection(self):
        mc = get_meta_controller()
        mc.adapt({
            "strategy_success": True,
            "interaction_type": "contradiction",
            "significance": 0.9,
        })
        assert mc.get_state() == CognitiveState.REFLECTING
        mc.adapt({
            "strategy_success": True,
            "interaction_type": "new_knowledge",
            "significance": 0.1,
        })
        assert mc.get_state() == CognitiveState.IDLE

    def test_get_stats(self):
        mc = get_meta_controller()
        stats = mc.get_stats()
        assert "state" in stats
        assert stats["state"] == "idle"
