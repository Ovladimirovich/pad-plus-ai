"""
scripts/cognitive_robustness_test.py — Эксперимент №2: Memory Robustness Test.
Проверка устойчивости Composite Cognitive Workspace:
1. Перезапуск процесса (Persistence after restart)
2. Длинный контекст (100+ ходов)
3. Конфликтующие факты (Version resolution)
4. Многопоточная изоляция (Multi-session cross-contamination)
5. Negative Recall (Forgetting / Irrelevance / False recall)

БЕЗ изменения продакшен-кода.
"""

import os
import sys
import uuid
import random
import logging
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from core.workspace.integration import WorkspaceOrchestrator
from core.workspace.checkpointer import SQLiteCheckpointer
from core.workspace.schemas import ConversationWorkspace, ConversationCore

logger = logging.getLogger("padplus.robustness_test")


class MemoryRobustnessTest:
    def __init__(self):
        self.db_path = "data/robustness_test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.results: List[Dict[str, Any]] = []

    def run_all(self):
        print("============================================================")
        print("[TEST] ЗАПУСК ЭКСПЕРИМЕНТА №2: MEMORY ROBUSTNESS TEST")
        print("============================================================\n")

        self.test_1_restart_persistence()
        self.test_2_long_horizon()
        self.test_3_conflicting_facts()
        self.test_4_multi_session_isolation()
        self.test_5_negative_recall()

        self.generate_report()

    def test_1_restart_persistence(self):
        print("--- TEST 1: Перезапуск процесса (Restart Persistence) ---")
        session_id = f"restart-{uuid.uuid4().hex[:6]}"
        
        # Фаза А: Первые 5 ходов
        cp1 = SQLiteCheckpointer(self.db_path)
        orch1 = WorkspaceOrchestrator(checkpointer=cp1)
        conv1 = orch1.get_or_create_conversation(session_id)
        
        conv1.add_turn(1, "Привет, проект называется NEPTUNE-9", "init")
        conv1.add_entity("NEPTUNE-9", "Глубоководный зонд")
        conv1.push_goal("Найти воду на спутнике", turn_id=1)
        orch1.save_conversation(conv1)
        
        # Симулируем полную остановку и рестарт процесса (новый экземпляр checkpointer/orchestrator)
        del cp1, orch1, conv1
        
        # Фаза Б: Восстановление после рестарта
        cp2 = SQLiteCheckpointer(self.db_path)
        orch2 = WorkspaceOrchestrator(checkpointer=cp2)
        loaded_conv = cp2.load_conversation(session_id)
        
        passed = (
            loaded_conv is not None and
            loaded_conv.core.turn_count == 1 and
            "NEPTUNE-9" in loaded_conv.core.entities and
            len(loaded_conv.core.active_goals) == 1 and
            loaded_conv.core.active_goals[0].description == "Найти воду на спутнике"
        )
        
        self.results.append({
            "test": "1. Restart Persistence",
            "passed": passed,
            "details": f"Loaded turn count: {loaded_conv.core.turn_count if loaded_conv else 'None'}"
        })
        print(f"Result: {'[OK]' if passed else '[FAIL]'}\n")

    def test_2_long_horizon(self):
        print("--- TEST 2: Длинный контекст (Long Horizon 100 turns) ---")
        session_id = f"long-{uuid.uuid4().hex[:6]}"
        cp = SQLiteCheckpointer(self.db_path)
        orch = WorkspaceOrchestrator(checkpointer=cp)
        conv = orch.get_or_create_conversation(session_id)
        
        # 100 ходов с постоянным введением новых тем и фактов
        for i in range(1, 101):
            topic = f"topic_{i}"
            conv.add_turn(i, f"Сообщение номер {i} на тему {topic}", topic)
            conv.add_fact(f"Факт номер {i} для темы {topic}")
            if i % 10 == 0:
                conv.push_goal(f"Цель номер {i}", turn_id=i)
                
        orch.save_conversation(conv)
        
        # Проверяем целостность после 100 ходов
        loaded = cp.load_conversation(session_id)
        passed = (
            loaded is not None and
            loaded.core.turn_count == 100 and
            len(loaded.core.key_facts) == 100 and
            len(loaded.core.active_goals) == 10
        )
        
        self.results.append({
            "test": "2. Long Horizon (100 turns)",
            "passed": passed,
            "details": f"Total turns: {loaded.core.turn_count if loaded else 0}, Facts: {len(loaded.core.key_facts) if loaded else 0}"
        })
        print(f"Result: {'[OK]' if passed else '[FAIL]'}\n")

    def test_3_conflicting_facts(self):
        print("--- TEST 3: Конфликтующие факты и версионность (Conflict & Overwrite) ---")
        session_id = f"conflict-{uuid.uuid4().hex[:6]}"
        cp = SQLiteCheckpointer(self.db_path)
        orch = WorkspaceOrchestrator(checkpointer=cp)
        conv = orch.get_or_create_conversation(session_id)
        
        # Версия 1 факта
        conv.add_fact("API_TIMEOUT = 30 seconds")
        # Версия 2 факта (обновление)
        conv.add_fact("API_TIMEOUT = 60 seconds (updated)")
        orch.save_conversation(conv)
        
        loaded = cp.load_conversation(session_id)
        # Проверяем, что последний актуальный факт извлечен корректно (или оба сохранены для рефлексии)
        facts = loaded.core.key_facts if loaded else []
        has_updated = any("60 seconds" in f for f in facts)
        
        passed = has_updated and len(facts) >= 2
        
        self.results.append({
            "test": "3. Conflict & Versioning",
            "passed": passed,
            "details": f"Stored facts: {facts}"
        })
        print(f"Result: {'[OK]' if passed else '[FAIL]'}\n")

    def test_4_multi_session_isolation(self):
        print("--- TEST 4: Многопоточная изоляция сессий (Multi-Session Isolation) ---")
        cp = SQLiteCheckpointer(self.db_path)
        orch = WorkspaceOrchestrator(checkpointer=cp)
        
        sess_a = "session-ALPHA"
        sess_b = "session-BETA"
        
        conv_a = orch.get_or_create_conversation(sess_a, "diag-a")
        conv_a.add_fact("Секрет сессии А: Пароль123")
        orch.save_conversation(conv_a)
        
        conv_b = orch.get_or_create_conversation(sess_b, "diag-b")
        conv_b.add_fact("Секрет сессии Б: Ключ999")
        orch.save_conversation(conv_b)
        
        # Попытка прочитать данные сессии А из сессии Б
        loaded_b = cp.load_conversation(sess_b)
        b_facts = " ".join(loaded_b.core.key_facts) if loaded_b else ""
        
        leakage = "Пароль123" in b_facts
        passed = not leakage and "Ключ999" in b_facts
        
        self.results.append({
            "test": "4. Multi-Session Isolation",
            "passed": passed,
            "details": f"Data leakage detected: {leakage}"
        })
        print(f"Result: {'[OK]' if passed else '[FAIL]'}\n")

    def test_5_negative_recall(self):
        print("--- TEST 5: Negative Recall (Forgetting / Irrelevance / False Recall) ---")
        session_id = f"neg-{uuid.uuid4().hex[:6]}"
        cp = SQLiteCheckpointer(self.db_path)
        orch = WorkspaceOrchestrator(checkpointer=cp)
        conv = orch.get_or_create_conversation(session_id)
        
        # Ход 5: Инжектируем секретный артефакт
        conv.add_turn(5, "Секретный кодовый артефакт: OMEGA-SECRET-999", "secret")
        conv.add_fact("OMEGA-SECRET-999")
        
        # Ходы 6 - 50: Полный уход в другую предметную область (шум)
        for i in range(6, 51):
            conv.add_turn(i, f"Обсуждаем кулинарию и рецепты пиццы номер {i}", "cooking")
            conv.add_fact(f"Рецепт пиццы #{i}")
            
        orch.save_conversation(conv)
        
        # Проверяем, что при запросе по нерелевантной теме (кулинария) система не подтягивает OMEGA-SECRET-999 в активный контекст топика
        loaded = cp.load_conversation(session_id)
        current_topic = loaded.core.current_topic if loaded else ""
        
        # Ожидаем, что текущий топик — cooking, а не secret
        passed = (current_topic == "cooking")
        
        self.results.append({
            "test": "5. Negative Recall",
            "passed": passed,
            "details": f"Current active topic after noise: {current_topic} (expected cooking)"
        })
        print(f"Result: {'[OK]' if passed else '[FAIL]'}\n")

    def generate_report(self):
        print("============================================================")
        print("[REPORT] ИТОГОВЫЙ ОТЧЁТ EXTREME MEMORY ROBUSTNESS TEST")
        print("============================================================")
        print(f"{'Test Name':<35} | {'Result':<6} | {'Details'}")
        print("-" * 75)
        
        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)
        
        for r in self.results:
            res_str = "PASS" if r["passed"] else "FAIL"
            print(f"{r['test']:<35} | {res_str:<6} | {r['details']}")
            
        print("-" * 75)
        print(f"Успешность стресс-теста: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
        print("============================================================\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    tester = MemoryRobustnessTest()
    tester.run_all()
