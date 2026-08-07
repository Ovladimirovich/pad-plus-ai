"""
Тест автономности (smoke против живого сервера).

Проверяет:
- /api/v1/chat (требует авторизации и LLM-ключа)
- /api/v1/mind-state (панель памяти/автономии)

Тесты скипаются, если сервер недоступен, отсутствует авторизация
или не настроен LLM-ключ.
"""

import pytest
import requests

BASE_URL = "http://localhost:8007/api/v1"


def _is_server_available():
    """Проверяет доступность сервера по реальному открытому эндпоинту"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def _is_chat_available():
    """Проверяет, доступен ли /chat без авторизации.

    Возвращает:
      'ok'    — эндпоинт отвечает (значит тест можно гонять)
      'auth'  — требуется авторизация / LLM-ключ → skip
    """
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"prompt": "привет"},
            timeout=3,
        )
        if response.status_code in (401, 403):
            return "auth"
        return "ok"
    except (requests.ConnectionError, requests.Timeout):
        return "auth"


@pytest.mark.integration
@pytest.mark.autonomy
@pytest.mark.slow
def test_chat_with_quality():
    """Тест чата со статусом качества"""
    if not _is_server_available():
        pytest.skip("Сервер не запущен на localhost:8007")
    if _is_chat_available() != "ok":
        pytest.skip("Для /chat требуется авторизация и настроенный LLM-ключ")
    print("\n🧪 Тест чата со статусом качества...")

    response = requests.post(
        f"{BASE_URL}/chat",
        json={"prompt": "Расскажи о себе кратко"},
    )

    assert response.status_code == 200
    data = response.json()
    print(f"✅ Ответ получен")
    print(f"   Provider: {data.get('provider')}")
    print(f"   RAG Used: {data.get('rag_used')}")

    assert "provider" in data
    assert "text" in data
    assert len(data["text"]) > 0

    return data


@pytest.mark.integration
@pytest.mark.autonomy
def test_autonomy_status():
    """Тест статуса автономии"""
    if not _is_server_available():
        pytest.skip("Сервер не запущен на localhost:8007")
    print("\n🧪 Тест статуса автономии...")

    response = requests.get(f"{BASE_URL}/mind-state")
    assert response.status_code == 200
    data = response.json()

    memory = data.get("memory", {})
    rag = memory.get("rag", {})
    print(f"✅ Статус получен")
    print(f"   Total Dialogs: {rag.get('total_dialogs')}")
    print(f"   Emotion: {list(data.get('emotion', {}).keys())[:3]}")

    # Проверяем наличие реальных сегментов панели
    assert "emotion" in data
    assert "memory" in data

    return data


@pytest.mark.integration
@pytest.mark.autonomy
def test_multiple_chats():
    """Несколько чатов для тестирования авто-рефлексии"""
    if not _is_server_available():
        pytest.skip("Сервер не запущен на localhost:8007")
    if _is_chat_available() != "ok":
        pytest.skip("Для /chat требуется авторизация и настроенный LLM-ключ")
    print("\n🧪 Тестирование нескольких диалогов...")

    prompts = [
        "Что такое искусственный интеллект?",
        "Как работает нейронная сеть?",
        "Объясни машинное обучение",
    ]

    results = []
    for prompt in prompts:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"prompt": prompt},
        )
        assert response.status_code == 200
        data = response.json()
        print(f"   Диалог: provider={data.get('provider')}, len={len(data.get('text', ''))}")
        results.append(data)

    assert len(results) == len(prompts)
    return results


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ТЕСТ АВТОНОМНОСТИ")
    print("=" * 50)

    test_chat_with_quality()
    test_autonomy_status()
    test_multiple_chats()

    print("\n✅ Тестирование завершено!")
    print("=" * 50)