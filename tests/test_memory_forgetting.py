import pytest
from memory.forgetting import PriorityForgetting, ForgetRecord, get_forgetting, reset_forgetting


@pytest.fixture(autouse=True)
def reset():
    reset_forgetting()
    yield
    forgetting = get_forgetting()
    forgetting.reset()
    reset_forgetting()


def _make_item(
    item_id: str = "1",
    significance: float = 0.5,
    access_count: int = 0,
    days_since_access: float = 30.0,
    confidence: float = 0.5,
):
    import time
    from datetime import datetime, timedelta
    return {
        "id": item_id,
        "significance": significance,
        "confidence": confidence,
        "access_count": access_count,
        "count": access_count,
        "last_accessed": time.time() - days_since_access * 86400,
        "knowledge_type": "declarative",
    }


class TestImportance:
    def test_high_importance(self):
        forgetting = PriorityForgetting()
        item = _make_item(significance=0.9, access_count=50, days_since_access=1)
        importance = forgetting.calculate_importance(item)
        assert importance > 0.5

    def test_low_importance(self):
        forgetting = PriorityForgetting()
        item = _make_item(significance=0.1, access_count=0, days_since_access=60)
        importance = forgetting.calculate_importance(item)
        assert importance < 0.3

    def test_no_last_accessed(self):
        forgetting = PriorityForgetting()
        item = {"id": "1", "significance": 0.5, "access_count": 0}
        importance = forgetting.calculate_importance(item)
        assert 0.0 <= importance <= 0.5


class TestRanking:
    def test_ranks_lowest_first(self):
        forgetting = PriorityForgetting()
        items = [
            _make_item("1", significance=0.1, access_count=0, days_since_access=60),
            _make_item("2", significance=0.9, access_count=50, days_since_access=1),
            _make_item("3", significance=0.5, access_count=5, days_since_access=10),
        ]
        ranked = forgetting.rank_for_targets(items)
        assert ranked[0]["importance"] <= ranked[1]["importance"] <= ranked[2]["importance"]

    def test_empty_items(self):
        forgetting = PriorityForgetting()
        ranked = forgetting.rank_for_targets([])
        assert ranked == []


class TestShouldForget:
    def test_low_importance_forgets(self):
        forgetting = PriorityForgetting(importance_threshold=0.3)
        item = _make_item(significance=0.1, access_count=0, days_since_access=60)
        reason = forgetting.should_forget(item, total_count=100)
        assert reason is not None
        assert "importance_too_low" in reason

    def test_high_importance_keeps(self):
        forgetting = PriorityForgetting(importance_threshold=0.3)
        item = _make_item(significance=0.9, access_count=100, days_since_access=1)
        reason = forgetting.should_forget(item, total_count=100)
        assert reason is None

    def test_storage_quota_triggers(self):
        forgetting = PriorityForgetting(storage_quota=10, importance_threshold=0.01)
        item = _make_item(significance=0.5, access_count=1, days_since_access=5)
        reason = forgetting.should_forget(item, total_count=100)
        assert reason is not None
        assert "storage_quota" in reason

    def test_high_importance_under_quota(self):
        forgetting = PriorityForgetting(storage_quota=1000, importance_threshold=0.5)
        item = _make_item(significance=0.9, access_count=100, days_since_access=1)
        reason = forgetting.should_forget(item, total_count=100)
        assert reason is None


class TestForgetBatch:
    def test_forgets_lowest_ranked(self):
        forgetting = PriorityForgetting(
            importance_threshold=0.3,
            forget_batch_size=10,
        )
        items = [_make_item(str(i), significance=0.1, access_count=0, days_since_access=60) for i in range(20)]
        items.append(_make_item("high", significance=0.9, access_count=100, days_since_access=1))
        records = forgetting.forget_lowest_ranked(items)
        assert len(records) > 0
        assert "high" not in [r.item_id for r in records]

    def test_respects_batch_size(self):
        forgetting = PriorityForgetting(
            importance_threshold=0.5,
            forget_batch_size=3,
        )
        items = [_make_item(str(i), significance=0.1, access_count=0, days_since_access=60) for i in range(10)]
        records = forgetting.forget_lowest_ranked(items)
        assert len(records) <= 3

    def test_empty_items_no_forgetting(self):
        forgetting = PriorityForgetting()
        records = forgetting.forget_lowest_ranked([])
        assert records == []

    def test_all_important_kept(self):
        forgetting = PriorityForgetting(importance_threshold=0.1)
        items = [_make_item(str(i), significance=0.9, access_count=50, days_since_access=1) for i in range(10)]
        records = forgetting.forget_lowest_ranked(items)
        assert len(records) == 0


class TestHistory:
    def test_records_after_forget(self):
        forgetting = PriorityForgetting(importance_threshold=0.5)
        items = [_make_item("1", significance=0.1, access_count=0, days_since_access=60)]
        forgetting.forget_lowest_ranked(items)
        history = forgetting.get_forgotten_history()
        assert len(history) == 1
        assert history[0]["item_id"] == "1"

    def test_get_stats(self):
        forgetting = PriorityForgetting(importance_threshold=0.5)
        items = [_make_item("1", significance=0.1, access_count=0, days_since_access=60)]
        forgetting.forget_lowest_ranked(items)
        stats = forgetting.get_stats()
        assert stats["total_forgotten"] == 1
        assert stats["importance_threshold"] == 0.5


class TestSingleton:
    def test_singleton(self):
        f1 = get_forgetting()
        f2 = get_forgetting()
        assert f1 is f2

    def test_reset_singleton(self):
        f1 = get_forgetting()
        reset_forgetting()
        f2 = get_forgetting()
        assert f1 is not f2
