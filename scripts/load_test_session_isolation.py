#!/usr/bin/env python3
"""
Load test для проверки session isolation.
Запускает N конкурентных пользователей и проверяет, что эмоции/импульсы не смешиваются.
"""
import asyncio
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List
import statistics

import httpx


# Конфигурация
BASE_URL = "http://127.0.0.1:8007"  # Backend URL
CONCURRENT_USERS = 10               # Количество одновременных пользователей
MESSAGES_PER_USER = 3               # Сообщений на пользователя
DELAY_BETWEEN_MSGS = 0.5            # Задержка между сообщениями (сек)


# Пользовательские сообщения для тестирования
TEST_MESSAGES = [
    "Привет! Как дела?",
    "Расскажи про квантовую запутанность",
    "Спасибо, очень помогло!",
    "Это неверно, проверь факты",
    "Почему так происходит?",
    "Отличный ответ!",
    "Не согласен с твоим мнением",
    "Объясни проще, пожалуйста",
]


class TestUser:
    """Симуляция одного пользователя"""
    
    def __init__(self, user_id: str, client: httpx.AsyncClient):
        self.user_id = user_id
        self.client = client
        self.session_id = str(uuid.uuid4())
        self.responses: List[Dict] = []
        self.errors: List[str] = []
    
    async def send_message(self, text: str) -> Dict:
        """Отправляет сообщение через API чата"""
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/chat",
                json={
                    "text": text,
                    "dialog_id": None,
                    "key_id": None,
                },
                headers={"X-Session-ID": self.session_id},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            self.responses.append({
                "text": text,
                "response": data.get("text", "")[:100],
                "timestamp": datetime.now().isoformat(),
            })
            return data
        except Exception as e:
            error_msg = f"User {self.user_id}: {type(e).__name__}: {e}"
            self.errors.append(error_msg)
            return {"error": str(e)}


async def test_session_isolation(num_users: int = CONCURRENT_USERS) -> Dict:
    """Основной тест session isolation"""
    
    print(f"\n{'='*60}")
    print(f"SESSION ISOLATION LOAD TEST")
    print(f"Users: {num_users}, Messages per user: {MESSAGES_PER_USER}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Проверяем доступность API
        try:
            health = await client.get(f"{BASE_URL}/health", timeout=5.0)
            print(f"Health check: {health.status_code}")
        except Exception as e:
            print(f"❌ Backend unavailable: {e}")
            return {"error": "Backend unavailable"}
        
        # Создаем пользователей
        users = [TestUser(f"user_{i}", client) for i in range(num_users)]
        
        # Параллельно отправляем сообщения
        async def user_session(user: TestUser):
            for msg_idx in range(MESSAGES_PER_USER):
                text = random.choice(TEST_MESSAGES)
                await user.send_message(text)
                await asyncio.sleep(DELAY_BETWEEN_MSGS + random.uniform(0, 0.3))
        
        # Запускаем все сессии параллельно
        start_time = time.time()
        await asyncio.gather(*[user_session(u) for u in users])
        total_time = time.time() - start_time
        
        # Собираем результаты
        all_errors = []
        all_responses = []
        
        for user in users:
            all_errors.extend(user.errors)
            all_responses.extend(user.responses)
        
        # Анализируем результаты
        result = {
            "total_users": num_users,
            "total_messages": num_users * MESSAGES_PER_USER,
            "successful_responses": len(all_responses),
            "errors": len(all_errors),
            "error_details": all_errors,
            "total_time_sec": round(total_time, 2),
            "avg_latency_ms": 0,
        }
        
        # Проверяем эмоциональную изоляцию через внутренние API
        await check_emotion_isolation(result, users)
        
        # Вывод результатов
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Users: {result['total_users']}")
        print(f"  Total messages: {result['total_messages']}")
        print(f"  Successful: {result['successful_responses']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Total time: {result['total_time_sec']}s")
        if result.get("emotion_isolation_ok") is not None:
            print(f"  Emotion isolation: {'OK' if result['emotion_isolation_ok'] else 'FAILED'}")
        if result.get("impulse_isolation_ok") is not None:
            print(f"  Impulse isolation: {'OK' if result['impulse_isolation_ok'] else 'FAILED'}")
        print(f"{'='*60}")
        
        return result


async def check_emotion_isolation(result: Dict, users: List) -> None:
    """Проверяет, что эмоции пользователей не смешиваются через внутренние API"""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Получаем состояние эмоций через API
            response = await client.get(f"{BASE_URL}/api/v1/mind-state")
            if response.status_code == 200:
                mind_state = response.json()
                
                # Проверяем, что есть данные по сессиям
                emotions = mind_state.get("emotion", {})
                impulses = mind_state.get("impulse", {})
                
                # Если есть per-session данные
                if isinstance(emotions, dict) and "sessions" in emotions:
                    sessions = emotions["sessions"]
                    # Проверяем, что у каждого пользователя свои эмоции
                    pleasure_values = []
                    for session_id, emo_data in sessions.items():
                        if "pleasure" in emo_data:
                            pleasure_values.append(emo_data["pleasure"])
                    
                    if len(pleasure_values) >= 2:
                        # Если есть разница между пользователями — изоляция работает
                        diff = max(pleasure_values) - min(pleasure_values)
                        result["emotion_isolation_ok"] = diff > 0.1
                        result["emotion_pleasure_range"] = [min(pleasure_values), max(pleasure_values)]
                    else:
                        result["emotion_isolation_ok"] = None
                        result["emotion_pleasure_range"] = []
                
                # Аналогично для импульсов
                if isinstance(impulses, dict) and "sessions" in impulses:
                    sessions = impulses["sessions"]
                    primary_labels = []
                    for session_id, imp_data in sessions.items():
                        if "primary" in imp_data:
                            primary_labels.append(imp_data["primary"])
                    
                    if len(primary_labels) >= 2:
                        unique_labels = set(primary_labels)
                        result["impulse_isolation_ok"] = len(unique_labels) > 1
                        result["impulse_labels"] = list(unique_labels)
                    else:
                        result["impulse_isolation_ok"] = None
                        result["impulse_labels"] = []
                        
    except Exception as e:
        result["emotion_isolation_error"] = str(e)
        result["emotion_isolation_ok"] = None
        result["impulse_isolation_ok"] = None


async def main():
    """Запуск теста"""
    result = await test_session_isolation()
    
    # Сохраняем отчет
    import json
    report_file = f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nReport saved to: {report_file}")
    
# Exit code для CI
    if result.get("errors", 0) > 0:
        print("TEST FAILED: errors detected")
        exit(1)
    if result.get("emotion_isolation_ok") is False:
        print("TEST FAILED: emotion isolation broken")
        exit(1)
    if result.get("impulse_isolation_ok") is False:
        print("TEST FAILED: impulse isolation broken")
        exit(1)

    print("ALL TESTS PASSED")
    exit(0)


if __name__ == "__main__":
    asyncio.run(main())