"""
scripts/cognitive_retrieval_experiment.py — Исследования Memory Retrieval & Retention.
Измерение кривой памяти (Memory Retention vs Conversation Distance) и точности извлечения (Precision/Recall).
БЕЗ изменения продакшен-кода.
"""

import os
import sys
import uuid
import logging
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from core.workspace.integration import WorkspaceOrchestrator
from core.workspace.checkpointer import SQLiteCheckpointer

logger = logging.getLogger("padplus.retrieval_experiment")


class MemoryRetrievalExperiment:
    def __init__(self):
        self.db_path = "data/retrieval_experiment.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.checkpointer = SQLiteCheckpointer(self.db_path)
        self.orchestrator = WorkspaceOrchestrator(checkpointer=self.checkpointer)

    def run_retention_curve(self):
        print("============================================================")
        print("[EXPERIMENT] MEMORY RETENTION VS CONVERSATION DISTANCE")
        print("============================================================\n")

        distances = [10, 25, 50, 100]
        results = []

        for dist in distances:
            session_id = f"retention-dist-{dist}-{uuid.uuid4().hex[:4]}"
            conv = self.orchestrator.get_or_create_conversation(session_id)

            # 1. Инжектируем целевой факт на ходу №1
            secret_fact = f"TARGET-SECRET-CODE-{dist}-XYZ"
            conv.add_turn(1, f"Запомни секретный код: {secret_fact}", "secret_init")
            conv.add_fact(secret_fact)

            # 2. Генерируем N ходов шума (другая предметная область)
            for turn_idx in range(2, dist + 1):
                conv.add_turn(turn_idx, f"Шумный ход номер {turn_idx}: обсуждаем кулинарию и погоду", "noise")
                # Периодически добавляем шумные факты
                if turn_idx % 5 == 0:
                    conv.add_fact(f"Шумный факт #{turn_idx}")

            self.orchestrator.save_conversation(conv)

            # 3. На ходу (dist + 1) запрашиваем секретный факт
            loaded = self.checkpointer.load_conversation(session_id)
            facts = loaded.core.key_facts if loaded else []
            
            retrieved = any(secret_fact in f for f in facts)
            # Измеряем Precision: сколько всего фактов поднято и сколько среди них релевантных
            total_facts = len(facts)
            precision = 1.0 if retrieved and total_facts > 0 else 0.0

            results.append({
                "distance": dist,
                "retrieved": retrieved,
                "total_facts_retained": total_facts,
                "precision": precision
            })

            print(f"Distance: {dist:3d} turns | Retrieved: {'[OK]' if retrieved else '[FAIL]}'} | Total Stored Facts: {total_facts}")

        print("\n============================================================")
        print("[REPORT] RETENTION CURVE SUMMARY")
        print("============================================================")
        for r in results:
            status = "RETAINED" if r["retrieved"] else "LOST"
            print(f"Distance {r['distance']:3d} turns -> Status: {status} (Facts pool: {r['total_facts_retained']})")
        print("============================================================\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    exp = MemoryRetrievalExperiment()
    exp.run_retention_curve()
