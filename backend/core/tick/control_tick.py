import asyncio
import logging
import os
import time
from typing import Optional

logger = logging.getLogger("padplus.tick")


class ControlTick:
    def __init__(self, interval: Optional[int] = None):
        self._interval = interval or int(os.getenv("CONTROL_TICK_INTERVAL", "300"))
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._tick_count = 0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("ControlTick started (interval=%ds)", self._interval)

    async def stop(self):
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("ControlTick stopped")

    async def _loop(self):
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("ControlTick error: %s", e)
            await asyncio.sleep(self._interval)

    async def _tick(self):
        self._tick_count += 1
        tick_id = self._tick_count
        logger.info("ControlTick #%d started", tick_id)
        start = time.time()

        results = {}

        # 1. Анализ последних оценок из DataCollector
        try:
            from learning.collector import get_collector
            collector = get_collector()
            recent = collector.export_dataset("dialogs", limit=10)
            results["recent_evaluations"] = len(recent)
        except Exception as e:
            logger.debug("ControlTick collector error: %s", e)
            results["recent_evaluations"] = 0

        # 2. MetaLearner — анализ паттернов
        try:
            from core.xray.meta_learner import get_meta_learner
            ml = get_meta_learner()
            patterns = ml.analyze_patterns()
            patterns_count = len(patterns.get("patterns", []))
            if patterns_count:
                logger.info("ControlTick: %d patterns detected", patterns_count)
            results["patterns"] = patterns_count
            results["recommendations"] = patterns.get("recommendations", [])
        except Exception as e:
            logger.debug("ControlTick meta_learner error: %s", e)
            results["patterns"] = 0

        # 3. ReflectionLoop — автономная рефлексия
        try:
            from core.xray.reflection import get_reflection_loop
            reflection = get_reflection_loop()
            results["reflection_stats"] = reflection.get_stats()
        except Exception as e:
            logger.debug("ControlTick reflection error: %s", e)

        # 4. Consolidation — проверка и запуск при необходимости
        try:
            from memory.consolidation import get_consolidator
            consolidator = get_consolidator()
            consolidator.run_scheduled_consolidation()
            results["consolidation"] = True
        except Exception as e:
            logger.debug("ControlTick consolidation error: %s", e)
            results["consolidation"] = False

        # 5. Публикация события tick_completed
        try:
            from core.events import get_events
            await get_events().tick_completed.publish({
                "tick_id": tick_id,
                "duration_ms": round((time.time() - start) * 1000, 2),
                "results": results,
            })
        except Exception as e:
            logger.debug("ControlTick event publish error: %s", e)

        logger.info(
            "ControlTick #%d completed in %.2fms",
            tick_id, (time.time() - start) * 1000,
        )

    def get_stats(self) -> dict:
        return {
            "tick_count": self._tick_count,
            "interval": self._interval,
            "running": self._running,
        }


_control_tick: Optional[ControlTick] = None


def get_control_tick() -> ControlTick:
    global _control_tick
    if _control_tick is None:
        _control_tick = ControlTick()
    return _control_tick


def reset_control_tick():
    global _control_tick
    _control_tick = None
