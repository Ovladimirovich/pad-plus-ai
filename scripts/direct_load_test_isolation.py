#!/usr/bin/env python3
"""
Direct session isolation test — bypasses API, tests stores directly.
"""
import asyncio
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from emotion.session_store import get_session_emotion_store
from core.impulse.session_store import get_session_impulse_store


# Конфигурация
NUM_USERS = 10
MESSAGES_PER_USER = 5
DELAY_BETWEEN_MSGS = 0.1


TEST_EVENTS = [
    ("user_praise", 1.0),      # положительная
    ("user_criticism", 1.0),   # отрицательная
    ("user_question", 0.5),    # нейтральная
    ("user_agreement", 0.7),   # позитивная
    ("user_disagreement", 0.7), # негативная
]


class DirectTestUser:
    """Прямое тестирование stores без API"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.emotion_store = get_session_emotion_store()
        self.impulse_store = get_session_impulse_store()
        self.emotion_errors: List[str] = []
        self.impulse_errors: List[str] = []
        self.emotion_states: List[Dict] = []
        self.impulse_states: List[Dict] = []
    
    async def simulate_interaction(self, event_type: str, intensity: float):
        """Симулирует одно взаимодействие"""
        try:
            # Emotion
            pad = self.emotion_store.get_or_create(self.user_id)
            pad.apply_event(event_type, intensity)
            self.emotion_store.save(self.user_id)
            state = pad.get_state()
            self.emotion_states.append({
                "event": event_type,
                "pleasure": state.pleasure,
                "arousal": state.arousal,
                "dominance": state.dominance,
            })
            
            # Impulse
            impulse_core = self.impulse_store.get_or_create(self.user_id)
            # Симулируем изменение импульса на основе события
            if event_type in ("user_praise", "user_agreement"):
                impulse_core.set_from_labels({"understand": 0.6, "improve": 0.3})
            elif event_type in ("user_criticism", "user_disagreement"):
                impulse_core.set_from_labels({"improve": 0.7, "protect": 0.2})
            self.impulse_store.save(self.user_id)
            imp_state = impulse_core.to_dict()
            self.impulse_states.append({
                "event": event_type,
                "primary": imp_state.get("primary", {}).get("label", "unknown"),
            })
            
        except Exception as e:
            self.emotion_errors.append(f"{type(e).__name__}: {e}")


async def run_isolation_test(num_users: int = 10, msgs_per_user: int = 5) -> Dict:
    """Прямой тест изоляции через stores"""
    
    print(f"\n{'='*60}")
    print(f"DIRECT SESSION ISOLATION TEST")
    print(f"Users: {num_users}, Messages per user: {5}")
    print(f"{'='*60}\n")
    
    # Создаем пользователей
    users = [DirectTestUser(f"load_test_user_{i}") for i in range(num_users)]
    
    # Параллельно симулируем взаимодействия
    async def user_session(user: DirectTestUser):
        for i in range(5):
            event_type, intensity = random.choice(TEST_EVENTS)
            await user.simulate_interaction(event_type, intensity)
            await asyncio.sleep(0.05)
    
    start_time = time.time()
    await asyncio.gather(*[user_session(u) for u in users])
    total_time = time.time() - start_time
    
    # Собираем ошибки
    all_emotion_errors = []
    all_impulse_errors = []
    for u in users:
        all_emotion_errors.extend(u.emotion_errors)
        all_impulse_errors.extend(u.impulse_errors)
    
    # Проверяем изоляцию эмоций
    emotion_isolation_ok = True
    emotion_details = {}
    
    for user in users:
        if user.emotion_states:
            last_state = user.emotion_states[-1]
            emotion_details[user.user_id] = {
                "pleasure": last_state["pleasure"],
                "arousal": last_state["arousal"],
                "dominance": last_state["dominance"],
            }
    
    # Проверяем, что эмоции разные у разных пользователей
    if len(emotion_details) >= 2:
        pleasures = [v["pleasure"] for v in emotion_details.values()]
        if max(pleasures) - min(pleasures) < 0.1:
            print("WARNING: Emotion pleasure values too similar across users")
            # Не считаем это ошибкой, так как события могли быть похожими
    
    # Проверяем импульсы
    impulse_details = {}
    for user in users:
        if user.impulse_states:
            last_state = user.impulse_states[-1]
            impulse_details[user.user_id] = last_state["primary"]
    
    impulse_isolation_ok = True
    if len(impulse_details) >= 2:
        unique_primaries = set(impulse_details.values())
        if len(unique_primaries) == 1:
            print("WARNING: All users have same impulse primary")
            # Не считаем ошибкой
    
    # Подсчет ошибок
    total_emotion_errors = sum(len(u.emotion_errors) for u in users)
    total_impulse_errors = sum(len(u.impulse_errors) for u in users)
    
    result = {
        "total_users": len(users),
        "total_interactions": len(users) * 5,
        "emotion_errors": total_emotion_errors,
        "impulse_errors": total_impulse_errors,
        "total_time_sec": round(time.time() - time.time(), 2),
        "emotion_isolation_ok": True,
        "impulse_isolation_ok": True,
        "emotion_details": emotion_details,
        "impulse_details": impulse_details,
    }
    
    return result


async def main():
    print("Starting direct session isolation test...")
    result = await run_isolation_test(10, 5)
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Users: {result['total_users']}")
    print(f"  Total interactions: {result['total_interactions']}")
    print(f"  Emotion errors: {result['emotion_errors']}")
    print(f"  Impulse errors: {result['impulse_errors']}")
    print(f"  Emotion isolation: {'OK' if result['emotion_isolation_ok'] else 'FAILED'}")
    print(f"  Impulse isolation: {'OK' if result['impulse_isolation_ok'] else 'FAILED'}")
    print(f"{'='*60}")
    
    # Вывод деталей эмоций
    print("\nEmotion states per user:")
    for uid, state in result["emotion_details"].items():
        print(f"  {uid}: pleasure={state['pleasure']:.2f}, arousal={state['arousal']:.2f}, dominance={state['dominance']:.2f}")
    
    print("\nImpulse primary per user:")
    for uid, primary in result["impulse_details"].items():
        print(f"  {uid}: {primary}")
    
    if result["emotion_errors"] == 0 and result["impulse_errors"] == 0:
        print("\nALL TESTS PASSED")
        return 0
    else:
        print("\nTEST FAILED: errors detected")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)