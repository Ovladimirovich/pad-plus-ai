import json
import os
from pathlib import Path
from datetime import date

import pytest

from learning.collector import DataCollector, get_collector, reset_collector, COLLECTIONS


@pytest.fixture
def temp_collector(tmp_path):
    return DataCollector(base_dir=tmp_path / "datasets")


class TestRecord:
    def test_record_dialog(self, temp_collector):
        c = temp_collector
        dialog_id = c.record_dialog("Привет", "Здравствуйте!", {"overall": 0.9})
        assert len(dialog_id) == 12

    def test_record_dialog_persists(self, temp_collector):
        c = temp_collector
        dialog_id = c.record_dialog("тест", "ответ", {"completeness": 0.8}, {"model": "gpt"})
        records = c.export_dataset("dialogs")
        assert len(records) == 1
        assert records[0]["id"] == dialog_id
        assert records[0]["prompt"] == "тест"
        assert records[0]["metadata"]["model"] == "gpt"

    def test_record_feedback(self, temp_collector):
        c = temp_collector
        dialog_id = c.record_dialog("вопрос", "ответ")
        c.record_feedback(dialog_id, "thumbs_up", 1.0)
        records = c.export_dataset("feedback")
        assert len(records) == 1
        assert records[0]["dialog_id"] == dialog_id

    def test_record_reward(self, temp_collector):
        c = temp_collector
        dialog_id = c.record_dialog("вопрос", "ответ")
        c.record_reward(dialog_id, 0.85)
        records = c.export_dataset("rewards")
        assert len(records) == 1
        assert records[0]["reward"] == 0.85


class TestExport:
    def test_export_empty(self, temp_collector):
        c = temp_collector
        records = c.export_dataset("dialogs")
        assert records == []

    def test_export_unknown_collection(self, temp_collector):
        c = temp_collector
        records = c.export_dataset("nonexistent")
        assert records == []

    def test_export_limit(self, temp_collector):
        c = temp_collector
        for i in range(10):
            c.record_dialog(f"вопрос {i}", f"ответ {i}")
        records = c.export_dataset("dialogs", limit=3)
        assert len(records) == 3

    def test_export_multiple_days(self, temp_collector):
        c = temp_collector
        c.record_dialog("первый", "ответ1")
        c.record_dialog("второй", "ответ2")
        records = c.export_dataset("dialogs")
        assert len(records) == 2


class TestStats:
    def test_empty_collection_stats(self, temp_collector):
        c = temp_collector
        stats = c.get_collection_stats("dialogs")
        assert stats["total"] == 0

    def test_collection_stats(self, temp_collector):
        c = temp_collector
        c.record_dialog("вопрос", "ответ")
        c.record_dialog("вопрос2", "ответ2")
        stats = c.get_collection_stats("dialogs")
        assert stats["total"] == 2

    def test_all_stats(self, temp_collector):
        c = temp_collector
        stats = c.get_all_stats()
        assert set(stats.keys()) == set(COLLECTIONS)
        for col in COLLECTIONS:
            assert stats[col]["total"] == 0

    def test_unknown_collection_stats(self, temp_collector):
        c = temp_collector
        stats = c.get_collection_stats("unknown")
        assert "error" in stats


class TestEdgeCases:
    def test_concurrent_writes(self, temp_collector):
        import threading
        c = temp_collector
        errors = []

        def writer(n):
            try:
                for _ in range(20):
                    c.record_dialog(f"вопрос {n}", f"ответ {n}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        records = c.export_dataset("dialogs")
        assert len(records) == 100

    def test_clear(self, temp_collector):
        c = temp_collector
        c.record_dialog("тест", "ответ")
        assert len(c.export_dataset("dialogs")) == 1
        c.clear()
        assert len(c.export_dataset("dialogs")) == 0


class TestSingleton:
    def test_get_collector(self):
        reset_collector()
        a = get_collector()
        b = get_collector()
        assert a is b

    def test_reset(self):
        reset_collector()
        a = get_collector()
        reset_collector()
        b = get_collector()
        assert a is not b
