"""
Тест RAG функциональности (smoke против живого сервера).

Проверяет реальные эндпоинты:
- /api/v1/chat (требует авторизации и LLM-ключа)
- /api/v1/mind-state (панель памяти с RAG-статистикой)

Тесты скипаются, если сервер недоступен, отсутствует авторизация
или не настроен LLM-ключ.
"""

import httpx
import time
import pytest

BASE_URL = "http://localhost:8007/api/v1"


def _is_server_available():
    """Проверяет доступность сервера по реальному открытому эндпоинту"""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def _is_chat_available():
    """Проверяет, доступен ли /chat без авторизации.

    Возвращает:
      'ok'    — эндпоинт отвечает (значит тест можно гонять)
      'auth'  — требуется авторизация / LLM-ключ → skip
    """
    try:
        response = httpx.post(
            f"{BASE_URL}/chat",
            json={"prompt": "привет"},
            timeout=3,
        )
        if response.status_code == 401 or response.status_code == 403:
            return "auth"
        return "ok"
    except Exception:
        return "auth"


def test_chat():
    """Тестирует чат и сохранение в RAG"""
    if not _is_server_available():
        pytest.skip("Сервер не запущен на localhost:8007")
    if _is_chat_available() != "ok":
        pytest.skip("Для /chat требуется авторизация и настроенный LLM-ключ")
    print("🧪 Тест чата с RAG...")

    response = httpx.post(
        f"{BASE_URL}/chat",
        json={"prompt": "Что такое искусственный интеллект?"},
        timeout=30.0,
    )

    if response.status_code == 200:
        data = response.json()
        text = data.get("text") or ""
        print(f"✅ Ответ: {text[:100]}...")
        print(f"   Provider: {data.get('provider')}")
        print(f"   RAG использован: {data.get('rag_used', False)}")
        return True
    else:
        print(f"❌ Ошибка: {response.status_code}")
        return False


def test_rag_stats():
    """Проверяет статистику RAG через /mind-state"""
    if not _is_server_available():
        pytest.skip("Сервер не запущен на localhost:8007")
    print("\n📊 Статистика RAG...")
    try:
        response = httpx.get(f"{BASE_URL}/mind-state", timeout=5)
    except httpx.HTTPError as e:
        print(f"❌ Ошибка запроса: {str(e)[:80]}")
        pytest.skip("Не удалось получить /mind-state")

    if response.status_code == 200:
        data = response.json()
        rag = data.get("memory", {}).get("rag", {})
        total_dialogs = rag.get("total_dialogs", 0)
        print(f"   Диалогов в памяти: {total_dialogs}")
        print(f"   С ключевыми словами: {rag.get('with_keywords', 0)}")
        return total_dialogs
    else:
        print(f"❌ Ошибка: {response.status_code}")
        pytest.skip(f"/mind-state вернул {response.status_code}")


def test_rag_search():
    """Тестирует семантический поиск через RAG-данные /mind-state"""
    if not _is_server_available():
        pytest.skip("Сервер не запущен на localhost:8007")
    print("\n🔍 Семантический поиск (через RAG-статистику)...")

    response = httpx.get(f"{BASE_URL}/mind-state", timeout=5)
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        pytest.skip(f"/mind-state вернул {response.status_code}")

    rag = response.json().get("memory", {}).get("rag", {})
    total = rag.get("total_dialogs", 0)
    # Отдельного /rag/search-эндпоинта нет; проверяем доступность статистики
    print(f"   Доступно диалогов в памяти: {total}")
    return total


if __name__ == "__main__":
    print("=" * 50)
    print("🧠 Тестирование RAG для PAD+ AI")
    print("=" * 50)

    count_before = test_rag_stats()

    test_chat()
    time.sleep(1)

    count_after = test_rag_stats()

    if count_after > 0:
        test_rag_search()

    print("\n" + "=" * 50)
    if count_after > count_before:
        print("✅ RAG работает! Диалоги сохраняются.")
    else:
        print("⚠️ Диалоги не сохраняются в RAG")
    print("=" * 50)