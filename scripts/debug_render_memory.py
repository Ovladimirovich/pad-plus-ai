#!/usr/bin/env python3
"""
🔍 Отладочный скрипт для проверки памяти в Render
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Отладочная информация о памяти")
print("=" * 60)

# Проверка 1: Какая база используется
print("\n1. Конфигурация базы данных:")
try:
    from core.config_manager import get_database_url
    db_url = get_database_url()
    print(f"   DATABASE_URL: {db_url[:80]}...")
    print(f"   Используется PostgreSQL: {db_url.startswith('postgresql')}")
except Exception as e:
    print(f"   Ошибка: {str(e)}")

# Проверка 2: Какие модули памяти загружены
print("\n2. Загруженные модули памяти:")
try:
    from memory import EpisodicMemory, SemanticMemory, get_episodic_memory, get_semantic_memory
    
    ep_mem = get_episodic_memory()
    sem_mem = get_semantic_memory()
    
    print(f"   EpisodicMemory: {type(ep_mem).__name__}")
    print(f"   EpisodicMemory модуль: {type(ep_mem).__module__}")
    print(f"   SemanticMemory: {type(sem_mem).__name__}")
    print(f"   SemanticMemory модуль: {type(sem_mem).__module__}")
    
    # Проверка подключения
    print(f"   EpisodicMemory подключение: {ep_mem._conn is not None}")
    print(f"   SemanticMemory подключение: {sem_mem._conn is not None}")
    
except Exception as e:
    print(f"   Ошибка: {str(e)}")

# Проверка 3: Прямой запрос к базе
print("\n3. Прямой запрос к базе данных:")
try:
    import psycopg2
    from core.config_manager import get_database_url
    
    conn = psycopg2.connect(get_database_url())
    cur = conn.cursor()
    
    # Проверка таблиц
    cur.execute("SELECT COUNT(*) FROM episodes")
    episodes_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM semantic_knowledge")
    knowledge_count = cur.fetchone()[0]
    
    # Проверка нескольких записей
    cur.execute("SELECT id, user_message FROM episodes LIMIT 3")
    episodes_sample = cur.fetchall()
    
    cur.execute("SELECT id, content FROM semantic_knowledge LIMIT 3")
    knowledge_sample = cur.fetchall()
    
    conn.close()
    
    print(f"   Эпизоды в базе: {episodes_count}")
    print(f"   Знания в базе: {knowledge_count}")
    print(f"   Пример эпизодов: {len(episodes_sample)}")
    print(f"   Пример знаний: {len(knowledge_sample)}")
    
    if episodes_count > 0:
        print(f"   Первый эпизод: {episodes_sample[0][0][:20]}... - {episodes_sample[0][1][:30]}...")
    if knowledge_count > 0:
        print(f"   Первое знание: {knowledge_sample[0][0][:20]}... - {knowledge_sample[0][1][:30]}...")
    
except Exception as e:
    print(f"   Ошибка: {str(e)}")

# Проверка 4: Данные через память
print("\n4. Данные через интерфейс памяти:")
try:
    from memory import get_episodic_memory, get_semantic_memory
    
    ep_mem = get_episodic_memory()
    sem_mem = get_semantic_memory()
    
    ep_stats = ep_mem.get_stats()
    sem_stats = sem_mem.get_stats()
    
    print(f"   Эпизоды через память: {ep_stats.get('total_episodes', 0)}")
    print(f"   Знания через память: {sem_stats.get('total_knowledge', 0)}")
    
    # Прямой поиск
    episodes = ep_mem.search_episodes(limit=3)
    knowledge = sem_mem.search_knowledge(limit=3)
    
    print(f"   Найдено эпизодов: {len(episodes)}")
    print(f"   Найдено знаний: {len(knowledge)}")
    
    if len(episodes) > 0:
        print(f"   Первый эпизод ID: {episodes[0].id}")
    if len(knowledge) > 0:
        print(f"   Первое знание ID: {knowledge[0].id}")
    
except Exception as e:
    print(f"   Ошибка: {str(e)}")

# Проверка 5: Сравнение
print("\n5. Сравнение:")
try:
    if episodes_count > 0 and ep_stats.get('total_episodes', 0) == 0:
        print("   ❌ Проблема: Данные есть в базе, но не загружаются в память")
        print("   Возможные причины:")
        print("   - Ошибка в методе get_stats()")
        print("   - Проблема с подключением памяти к базе")
        print("   - Ошибка в SQL-запросах")
    elif episodes_count == 0:
        print("   ❌ Проблема: Нет данных в базе PostgreSQL")
        print("   Возможные причины:")
        print("   - Данные сохранены в другой базе")
        print("   - Ошибка миграции")
        print("   - Проблема с сохранением данных")
    else:
        print("   ✅ Все работает нормально")
        print("   Данные загружаются из базы в память")
    
except Exception as e:
    print(f"   Ошибка: {str(e)}")

print("\n" + "=" * 60)
print("Рекомендации:")
print("=" * 60)

if episodes_count > 0 and ep_stats.get('total_episodes', 0) == 0:
    print("1. Проверить метод get_stats() в episodic_postgres.py")
    print("2. Проверить подключение к базе в памяти")
    print("3. Проверить SQL-запросы в get_stats()")
    print("4. Добавить логирование в метод get_stats()")
elif episodes_count == 0:
    print("1. Проверить миграцию 019 в Render")
    print("2. Проверить сохранение данных в базе")
    print("3. Убедиться, что данные сохраняются в правильную базу")
    print("4. Проверить подключение к Supabase")
else:
    print("1. Все работает нормально")
    print("2. Проблема может быть в другом месте")
    print("3. Проверить настройки фронтенда")
    print("4. Проверить API маршруты")