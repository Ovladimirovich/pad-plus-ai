from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAdminRoutes:
    def test_emotion_endpoint(self):
        with patch("emotion.emotion_learner.get_emotion_learner") as mock_learner, \
             patch("emotion.pad_model.get_pad_model") as mock_pad:
            mock_learner.return_value.get_stats.return_value = {
                "total_dialogs_analyzed": 5,
                "event_distribution": {"user_praise": 2},
                "recent_events": [],
            }
            mock_pad_instance = MagicMock()
            mock_pad_instance.pleasure = 0.5
            mock_pad_instance.arousal = 0.3
            mock_pad_instance.dominance = 0.7
            mock_pad.return_value = mock_pad_instance

            resp = client.get("/api/v1/admin/emotion")
            assert resp.status_code == 200
            data = resp.json()
            assert data["learner"]["total_dialogs_analyzed"] == 5
            assert data["pad"]["pleasure"] == 0.5

    def test_sync_status(self):
        with patch("core.pipeline.cross_memory_sync.get_cross_memory_sync") as mock_get:
            mock_sync = MagicMock()
            mock_sync._sync_count = 3
            mock_get.return_value = mock_sync

            resp = client.get("/api/v1/admin/sync")
            assert resp.status_code == 200
            assert resp.json()["sync_count"] == 3

    def test_trigger_sync(self):
        with patch("core.pipeline.cross_memory_sync.get_cross_memory_sync") as mock_get:
            mock_sync = MagicMock()
            mock_sync.sync_all.return_value = {
                "rag_to_semantic": ["a"],
                "episodic_to_semantic": ["b"],
                "semantic_to_roots": [],
            }
            mock_get.return_value = mock_sync

            # Use Bearer token to bypass CSRF
            resp = client.post(
                "/api/v1/admin/sync/trigger",
                headers={"Authorization": "Bearer test-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["total_insights"] == 2

    def test_health_endpoint(self):
        with patch("memory.consolidation.get_consolidator") as mock_cons, \
             patch("memory.get_rag") as mock_rag, \
             patch("emotion.emotion_learner.get_emotion_learner") as mock_learner, \
             patch("emotion.pad_model.get_pad_model") as mock_pad, \
             patch("core.pipeline.cross_memory_sync.get_cross_memory_sync") as mock_sync:
            mock_cons.return_value.get_consolidation_stats.return_value = {
                "total_consolidations": 10,
                "success_rate": 0.8,
            }
            mock_rag_instance = MagicMock()
            mock_rag_instance.get_stats.return_value = {"total_dialogs": 42}
            mock_rag.return_value = mock_rag_instance

            mock_learner.return_value.get_stats.return_value = {
                "total_dialogs_analyzed": 15,
                "event_distribution": {},
                "recent_events": [],
            }

            mock_pad_instance = MagicMock()
            mock_pad_instance.pleasure = 0.5
            mock_pad_instance.arousal = 0.3
            mock_pad_instance.dominance = 0.7
            mock_pad.return_value = mock_pad_instance

            mock_sync_instance = MagicMock()
            mock_sync_instance._sync_count = 5
            mock_sync.return_value = mock_sync_instance

            resp = client.get("/api/v1/admin/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["consolidation"]["total_consolidations"] == 10
            assert data["rag"]["total_dialogs"] == 42
            assert data["pad"]["pleasure"] == 0.5
            assert data["emotion_learner"]["total_dialogs_analyzed"] == 15
            assert "health_score" in data
            assert isinstance(data["suggestions"], list)
