"""
ImpulseManager — dual storage: PostgreSQL (priority) + JSON (always).

Паттерн как PADModel / emotion_state.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional

from .core import ImpulseCore

logger = logging.getLogger("padplus.impulse.manager")

from core.config import USE_PG_STORAGE


def _project_root() -> str:
    # backend/core/impulse/manager.py → parents[3] = repo root
    return str(Path(__file__).resolve().parents[3])


class ImpulseManager:
    """Менеджер импульса — load/save ядра импульсов."""

    DATA_DIR = "data"
    IMPULSE_FILE = "impulse.json"

    def __init__(self, base_path: str | None = None, use_pg: bool | None = None):
        if base_path is None:
            base_path = _project_root()
        self.base_path = base_path
        self.data_dir = os.path.join(base_path, self.DATA_DIR)
        self.impulse_path = os.path.join(self.data_dir, self.IMPULSE_FILE)
        self._core: Optional[ImpulseCore] = None
        self._lock = threading.RLock()
        self._use_pg = USE_PG_STORAGE if use_pg is None else use_pg
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def exists(self) -> bool:
        return os.path.exists(self.impulse_path)

    @property
    def core(self) -> Optional[ImpulseCore]:
        return self._core

    @core.setter
    def core(self, value: ImpulseCore):
        self._core = value

    def _load_from_pg(self) -> Optional[ImpulseCore]:
        if not self._use_pg:
            return None
        try:
            from core.pg_storage import PgStorage

            pg = PgStorage("impulse_state", mode="singleton")
            data = pg.load_singleton(lambda: {})
            if data and (data.get("version") is not None or data.get("primary") or data.get("question")):
                return ImpulseCore.from_dict(data)
        except Exception as e:
            logger.warning("Impulse PG load failed: %s", e)
        return None

    def _save_to_pg(self, core: ImpulseCore) -> None:
        if not self._use_pg:
            return
        try:
            from core.pg_storage import PgStorage

            pg = PgStorage("impulse_state", mode="singleton")
            pg.save_singleton(core.to_dict())
        except Exception as e:
            logger.warning("Impulse PG save failed: %s", e)

    def start(self) -> dict:
        with self._lock:
            # PG → JSON → default
            pg_core = self._load_from_pg()
            if pg_core is not None:
                self._core = pg_core
                # mirror to JSON for local consistency
                self._save_json(pg_core)
                return pg_core.to_dict()

            if self.exists():
                return self.load().to_dict()

            core = ImpulseCore()
            self.save(core)
            logger.info("Impulse started (default): %s", core.get_primary_question())
            return core.to_dict()

    def load(self) -> ImpulseCore:
        """Загружает impulse. PG first, затем JSON. FileNotFoundError если нет нигде."""
        with self._lock:
            pg_core = self._load_from_pg()
            if pg_core is not None:
                self._core = pg_core
                return self._core

            if not self.exists():
                raise FileNotFoundError("Импульс не найден")

            with open(self.impulse_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._core = ImpulseCore.from_dict(data)
            return self._core

    def _save_json(self, core: ImpulseCore) -> None:
        self._ensure_data_dir()
        with open(self.impulse_path, "w", encoding="utf-8") as f:
            f.write(core.to_json())
        self._sync_prompt_file(core)

    def save(self, core: ImpulseCore) -> None:
        with self._lock:
            self._core = core
            self._save_to_pg(core)
            self._save_json(core)

    def _sync_prompt_file(self, core: ImpulseCore) -> None:
        prompt_path = os.path.join(self.data_dir, "current_impulse.txt")
        prompt = core.get_prompt_line()
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

    def is_initialized(self) -> bool:
        if self.exists():
            return True
        pg_core = self._load_from_pg()
        return pg_core is not None


# ── Module-level API ──────────────────────────────────────────────

_manager: Optional[ImpulseManager] = None
_manager_lock = threading.Lock()


def reset_manager() -> None:
    """Сброс singleton (для тестов)."""
    global _manager
    with _manager_lock:
        _manager = None


def get_manager(base_path: str | None = None) -> ImpulseManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = ImpulseManager(base_path=base_path)
        return _manager


def start_impulse() -> dict:
    return get_manager().start()


def is_impulse_initialized() -> bool:
    return get_manager().is_initialized()


def get_impulse_core() -> ImpulseCore:
    mgr = get_manager()
    with mgr._lock:
        if mgr.core is None:
            try:
                mgr.load()
            except FileNotFoundError:
                mgr.start()
        return mgr.core


def set_impulse(weights: dict[str, float]) -> None:
    core = get_impulse_core()
    core.set_from_labels(weights)
    get_manager().save(core)


def set_impulse_by_question(question: str) -> None:
    core = get_impulse_core()
    core.set_from_question(question)
    get_manager().save(core)


def push_impulse() -> None:
    core = get_impulse_core()
    core.push()
    get_manager().save(core)


def pop_impulse() -> bool:
    core = get_impulse_core()
    result = core.pop()
    get_manager().save(core)
    return result
