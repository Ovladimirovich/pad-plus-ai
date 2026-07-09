"""
Production Diagnostic Script for PAD+ AI v4.0

Цель: Проверить состояние всех когнитивных компонентов на Render.
Вывод: Таблица состояния каждого компонента с доказательствами.

Запуск:
    python diagnostic_production.py

Вывод:
    | Компонент     | Работает | Доказательство                     | Причина (если не работает) |
    |---------------|----------|------------------------------------|----------------------------|
    | PostgreSQL    | [+]/[-]  | Соединение установлено             | pgvector отсутствует       |
    | RAG           | [+]/[-]  | Найдено 5 документов                | Ошибка подключения         |
    | Persona       | [+]/[-]  | Контекст: "Я — PAD+ AI..."         | Файл не найден             |
    | Emotion       | [+]/[-]  | Уверенность: 0.72                   | Ошибка загрузки            |
    | Episodic      | [+]/[-]  | Найдено 3 эпизода                   | Таблица не создана         |
    | Consolidation | [+]/[-]  | Обработано 2 эпизода                | Ошибка сигнатуры           |
    | Roots         | [+]/[-]  | Загружено 12 принципов              | Ошибка импорта             |
    | Generate      | [+]/[-]  | Контекст собран                     | LLM не отвечает            |

"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)
logger = logging.getLogger("PAD+.diagnostic")

# Добавляем корень проекта в sys.path
_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")


# ============================================================================
# ДИАГНОСТИЧЕСКИЕ ФУНКЦИИ
# ============================================================================

async def check_postgresql():
    """Проверка PostgreSQL: соединение, схема, pgvector"""
    result = {
        "component": "PostgreSQL",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        import psycopg2
        from psycopg2 import sql
        
        # Проверка соединения
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        result["details"]["connection"] = "✅ Установлено"
        
        # Проверка pgvector
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
            pgvector_installed = cur.fetchone() is not None
            result["details"]["pgvector"] = "✅ Установлен" if pgvector_installed else "❌ Отсутствует"
            
            # Проверка таблиц
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tables = [row[0] for row in cur.fetchall()]
            result["details"]["tables"] = f"Найдено {len(tables)} таблиц"
            
        conn.close()
        result["works"] = pgvector_installed
        result["proof"] = f"Соединение: ✅, pgvector: {'✅' if pgvector_installed else '❌'}"
        
    except ImportError:
        result["reason"] = "psycopg2 не установлен"
        result["proof"] = "❌ psycopg2 отсутствует"
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_rag():
    """Проверка RAG: документы, embedding, поиск"""
    result = {
        "component": "RAG",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from memory.rag_postgres import get_rag
        rag = get_rag()
        
        # Проверка загрузки документов
        stats = rag.get_stats()
        result["details"]["documents"] = f"Загружено: {stats.get('documents', 0)}"
        
        # Проверка поиска
        test_query = "Что такое PAD+ AI?"
        context = rag.get_context(test_query)
        
        if context:
            result["works"] = True
            result["proof"] = f"Поиск работает: {len(context)} символов"
            result["details"]["search"] = "✅ Успешно"
        else:
            result["reason"] = "Поиск не вернул результатов"
            result["proof"] = "❌ Поиск пустой"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_episodic():
    """Проверка эпизодической памяти: создание, поиск эпизодов"""
    result = {
        "component": "Episodic",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from memory.episodic import get_episodic_memory
        episodic = get_episodic_memory()
        
        # Проверка создания эпизода
        test_episode = {
            "user_message": "Тестовый запрос для диагностики",
            "ai_response": "Тестовый ответ",
            "topic": "диагностика",
            "intent": "тест",
            "emotion_before": {"confidence": 0.5},
            "emotion_after": {"confidence": 0.7}
        }
        
        episode_id = episodic.add_episode(**test_episode)
        result["details"]["create"] = f"✅ Эпизод создан: {episode_id}"
        
        # Проверка поиска
        similar = episodic.search_episodes("тестовый запрос", limit=1)
        if similar:
            result["works"] = True
            result["proof"] = f"Поиск работает: найдено {len(similar)} эпизодов"
            result["details"]["search"] = "✅ Успешно"
        else:
            result["reason"] = "Поиск не вернул результатов"
            result["proof"] = "❌ Поиск пустой"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_semantic():
    """Проверка семантической памяти: добавление, поиск знаний"""
    result = {
        "component": "Semantic",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from memory.semantic import get_semantic_memory, KnowledgeType
        semantic = get_semantic_memory()
        
        # Проверка добавления знания
        test_knowledge = {
            "content": "PAD+ AI — когнитивный слой для LLM",
            "knowledge_type": KnowledgeType.DECLARATIVE,
            "summary": "Определение PAD+ AI"
        }
        
        knowledge_id = semantic.add_knowledge(**test_knowledge)
        result["details"]["create"] = f"✅ Знание добавлено: {knowledge_id}"
        
        # Проверка поиска
        results = semantic.search_knowledge("когнитивный слой", limit=1)
        if results:
            result["works"] = True
            result["proof"] = f"Поиск работает: найдено {len(results)} знаний"
            result["details"]["search"] = "✅ Успешно"
        else:
            result["reason"] = "Поиск не вернул результатов"
            result["proof"] = "❌ Поиск пустой"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_consolidation():
    """Проверка консолидации: перенос эпизодов в семантическую память"""
    result = {
        "component": "Consolidation",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from memory.consolidation import MemoryConsolidator
        consolidator = MemoryConsolidator()
        
        # Проверка консолидации
        result_consolidation = await consolidator.consolidate_episodic_to_semantic()
        
        if result_consolidation.items_consolidated > 0:
            result["works"] = True
            result["proof"] = f"Консолидация работает: обработано {result_consolidation.items_processed} эпизодов"
            result["details"]["consolidation"] = "✅ Успешно"
        else:
            result["reason"] = "Нет эпизодов для консолидации"
            result["proof"] = "⚠️ Нет данных"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_persona():
    """Проверка Persona: загрузка, контекст"""
    result = {
        "component": "Persona",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from memory.persona import get_persona
        persona = get_persona()
        
        context = persona.get_persona_context()
        if context:
            result["works"] = True
            result["proof"] = f"Persona загружена: {len(context)} символов"
            result["details"]["context"] = "✅ Контекст доступен"
        else:
            result["reason"] = "Контекст пустой"
            result["proof"] = "❌ Контекст отсутствует"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_emotion():
    """Проверка Emotion: состояние, стиль"""
    result = {
        "component": "Emotion",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from emotion.pad_model import get_pad_model
        pad = get_pad_model()
        
        state = pad.get_state()
        style = pad.get_style()
        
        if state and style:
            result["works"] = True
            result["proof"] = f"Emotion работает: уверенность {state.confidence:.2f}, тон {style.get('tone', 'unknown')}"
            result["details"]["state"] = f"Уверенность: {state.confidence:.2f}"
        else:
            result["reason"] = "Состояние или стиль пустые"
            result["proof"] = "❌ Данные отсутствуют"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_roots():
    """Проверка Roots: загрузка принципов"""
    result = {
        "component": "Roots",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from memory.roots import get_roots_memory
        roots = get_roots_memory()
        
        context = roots.export_for_context()
        if context:
            result["works"] = True
            result["proof"] = f"Roots загружены: {len(context)} символов"
            result["details"]["principles"] = "✅ Принципы доступны"
        else:
            result["reason"] = "Контекст пустой"
            result["proof"] = "❌ Контекст отсутствует"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_generate_context():
    """Проверка сборки контекста для Generate"""
    result = {
        "component": "Generate Context",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from core.pipeline import get_pipeline
        from core.pipeline.context import PipelineContext
        
        # Создаем тестовый контекст
        ctx = PipelineContext(
            user_message="Тестовый запрос для диагностики контекста",
            context={"user_id": "diagnostic_user"}
        )
        
        pipeline = get_pipeline()
        
        # Запускаем только фазы формирования контекста
        phases = ["roots", "persona", "rag", "episodic", "emotion"]
        context_data = {}
        
        for phase_name in phases:
            phase = pipeline._phases.get(phase_name)
            if phase:
                phase_result = await phase.execute(ctx)
                if phase_result.success:
                    context_data.update(phase_result.data)
        
        # Проверяем наличие контекста
        missing = [k for k, v in context_data.items() if not v]
        present = [k for k, v in context_data.items() if v]
        
        if present:
            result["works"] = True
            result["proof"] = f"Контекст собран: {', '.join(present)}"
            result["details"]["context"] = f"Присутствует: {len(present)}, отсутствует: {len(missing)}"
        else:
            result["reason"] = f"Контекст пустой: отсутствует {', '.join(missing)}"
            result["proof"] = "❌ Контекст не собран"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


async def check_llm_service():
    """Проверка LLM Service: генерация ответа"""
    result = {
        "component": "LLM Service",
        "works": False,
        "proof": "",
        "reason": "",
        "details": {}
    }
    
    try:
        from runtime.llm_service import get_llm_service
        llm = get_llm_service()
        
        # Проверка генерации
        test_prompt = "Привет! Как тебя зовут?"
        response = await llm.generate(
            prompt=test_prompt,
            system_prompt="Ты — PAD+ AI, когнитивный ассистент.",
            api_key=os.getenv("TEST_API_KEY", "test"),
            model="test-model",
            provider="test-provider"
        )
        
        if response and response.text:
            result["works"] = True
            result["proof"] = f"LLM отвечает: {len(response.text)} символов"
            result["details"]["response"] = "✅ Ответ получен"
        else:
            result["reason"] = "Ответ пустой"
            result["proof"] = "❌ Ответ отсутствует"
            
    except Exception as e:
        result["reason"] = str(e)
        result["proof"] = f"❌ Ошибка: {str(e)[:50]}..."
    
    return result


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

async def run_diagnostic():
    """Запуск полной диагностики"""
    print("Запуск диагностики PAD+ AI v4.0 Production...")
    print("=" * 80)
    
    checks = [
        check_postgresql(),
        check_rag(),
        check_episodic(),
        check_semantic(),
        check_consolidation(),
        check_persona(),
        check_emotion(),
        check_roots(),
        check_generate_context(),
        check_llm_service()
    ]
    
    results = await asyncio.gather(*checks)
    
    # Формируем таблицу результатов
    print("\nРЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
    print("-" * 80)
    print(f"{'Компонент':<16} | {'Работает':<8} | {'Доказательство':<40} | {'Причина':<30}")
    print("-" * 80)
    
    for result in results:
        status = "OK" if result["works"] else "FAIL"
        proof = result['proof'].encode('ascii', 'ignore').decode('ascii') if result['proof'] else "-"
        reason = result.get('reason', '-').encode('ascii', 'ignore').decode('ascii') if result.get('reason') else "-"
        print(f"{result['component']:<16} | {status:<8} | {proof:<40} | {reason:<30}")
    
    print("\nДЕТАЛИ:")
    print("-" * 80)
    
    for result in results:
        print(f"\n[{result['component']}]:")
        for k, v in result["details"].items():
            detail = str(v).encode('ascii', 'ignore').decode('ascii') if v else "-"
            print(f"  - {k}: {detail}")
    
    # Итоговый анализ
    working = sum(1 for r in results if r["works"])
    total = len(results)
    print("\nИТОГ:")
    print(f"Работает: {working}/{total} компонентов")
    
    if working < total:
        print("\nПРОБЛЕМЫ ОБНАРУЖЕНЫ:")
        for result in results:
            if not result["works"]:
                print(f"  - {result['component']}: {result['reason']}")
    else:
        print("\nВсе компоненты работают корректно!")


if __name__ == "__main__":
    asyncio.run(run_diagnostic())