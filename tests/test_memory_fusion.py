import pytest
from memory.fusion import MemoryFusion, FusionRecord, get_fusion, reset_fusion


@pytest.fixture(autouse=True)
def reset():
    reset_fusion()
    yield
    fusion = get_fusion()
    fusion.reset()
    reset_fusion()


class TestJaccard:
    def test_same_text(self):
        fusion = MemoryFusion()
        sim = fusion._jaccard_similarity("кот сидит на окне", "кот сидит на окне")
        assert sim == 1.0

    def test_different_text(self):
        fusion = MemoryFusion()
        sim = fusion._jaccard_similarity("кот сидит на окне", "ракета летит в космос")
        assert sim < 0.3

    def test_partial_overlap(self):
        fusion = MemoryFusion()
        sim = fusion._jaccard_similarity("кот сидит на окне", "кот спит на диване")
        assert 0.1 < sim < 0.5

    def test_empty_text(self):
        fusion = MemoryFusion()
        sim = fusion._jaccard_similarity("", "кот")
        assert sim == 0.0


class TestFindCandidates:
    def test_finds_episodic_semantic_match(self):
        fusion = MemoryFusion()
        ep = [{"id": "1", "user_message": "расскажи про фотосинтез", "ai_response": "фотосинтез это процесс преобразования света в энергию в растениях основной источник", "significance": 0.8}]
        sem = [{"id": "2", "content": "фотосинтез это процесс преобразования света в энергию в растениях основной источник кислорода", "confidence": 0.9, "knowledge_type": "declarative"}]
        candidates = fusion.find_candidates(ep, sem)
        assert len(candidates) > 0

    def test_no_match_different_topics(self):
        fusion = MemoryFusion()
        ep = [{"id": "1", "user_message": "кот сидит на окне", "ai_response": "да, коты любят сидеть на окнах", "significance": 0.5}]
        sem = [{"id": "2", "content": "квантовая физика изучает элементарные частицы", "confidence": 0.9, "knowledge_type": "declarative"}]
        candidates = fusion.find_candidates(ep, sem)
        assert len(candidates) == 0

    def test_short_text_skipped(self):
        fusion = MemoryFusion()
        ep = [{"id": "1", "user_message": "да", "ai_response": "ок", "significance": 0.5}]
        candidates = fusion.find_candidates(ep, [])
        assert len(candidates) == 0


class TestFuse:
    def test_merges_content_longer_wins(self):
        fusion = MemoryFusion()
        a = {"content": "короткий текст", "confidence": 0.7, "access_count": 3, "tags": ["наука"]}
        b = {"content": "длинный текст с более подробным описанием темы", "confidence": 0.9, "access_count": 5, "tags": ["наука", "физика"]}
        merged = fusion.fuse(a, b, 0.85)
        assert merged["content"] == b["content"]
        assert merged["confidence"] == 0.8
        assert merged["access_count"] == 8
        assert "физика" in merged["tags"]

    def test_preserves_metadata(self):
        fusion = MemoryFusion()
        a = {"user_message": "вопрос", "significance": 0.8, "count": 2, "keywords": ["test"], "topic": "наука"}
        b = {"user_message": "ответ с информацией", "significance": 0.6, "count": 4, "keywords": ["test", "data"]}
        merged = fusion.fuse(a, b, 0.75)
        assert merged["confidence"] == 0.7
        assert merged["access_count"] == 6
        assert merged["topic"] == "наука"


class TestHistory:
    def test_records_fusion(self):
        fusion = MemoryFusion()
        record = FusionRecord(
            source_ids=["1", "2"],
            target_type="declarative",
            target_id="3",
            merged_fields={"content": "merged"},
            similarity=0.85,
        )
        fusion.record_fusion(record)
        history = fusion.get_history()
        assert len(history) == 1
        assert history[0]["similarity"] == 0.85

    def test_history_capped(self):
        fusion = MemoryFusion()
        for i in range(60):
            fusion.record_fusion(FusionRecord(source_ids=[str(i)], target_id=str(i)))
        assert len(fusion.get_history(limit=100)) == 50

    def test_get_stats(self):
        fusion = MemoryFusion()
        fusion.record_fusion(FusionRecord(source_ids=["a", "b"], similarity=0.9))
        stats = fusion.get_stats()
        assert stats["total_fusions"] == 1


class TestSingleton:
    def test_singleton(self):
        f1 = get_fusion()
        f2 = get_fusion()
        assert f1 is f2

    def test_reset_singleton(self):
        f1 = get_fusion()
        reset_fusion()
        f2 = get_fusion()
        assert f1 is not f2
