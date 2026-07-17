"""
P2 — Storage consistency tests.

Проверяет:
- USE_PG_STORAGE импортируется из единого core.config
- Все модули пишут JSON-файл как fallback (dual-write)
- Переключение через env USE_PG_STORAGE=false работает
"""

import os
import json
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


class TestUsePgConfig:
    """USE_PG_STORAGE читается из core.config во всех модулях"""

    def test_core_config_flag_exists(self):
        from core.config import USE_PG_STORAGE
        assert USE_PG_STORAGE in (True, False)

    def test_core_config_env_false(self):
        with patch.dict(os.environ, {"USE_PG_STORAGE": "false"}):
            import importlib
            import core.config
            importlib.reload(core.config)
            from core.config import USE_PG_STORAGE
            assert USE_PG_STORAGE is False

    def test_persona_uses_core_config(self):
        import memory.persona
        assert hasattr(memory.persona, "USE_PG_STORAGE")

    def test_pad_model_uses_core_config(self):
        import emotion.pad_model
        assert hasattr(emotion.pad_model, "USE_PG_STORAGE")

    def test_roots_uses_core_config(self):
        import memory.roots
        assert hasattr(memory.roots, "USE_PG_STORAGE")

    def test_impulse_uses_core_config(self):
        import core.impulse.manager
        assert hasattr(core.impulse.manager, "USE_PG_STORAGE")


class TestJsonFallback:
    """Все модули пишут JSON при save"""

    def test_persona_saves_json(self, tmp_path):
        from memory.persona import PersonaMemory
        json_path = tmp_path / "persona.json"
        p = PersonaMemory(storage_path=str(json_path))
        p._save()
        assert json_path.exists()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert "traits" in data

    def test_roots_saves_json(self, tmp_path):
        from memory.roots import RootsMemory
        json_path = tmp_path / "roots.json"
        r = RootsMemory(data_path=str(json_path))
        r._save()
        assert json_path.exists()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert "roots" in data
