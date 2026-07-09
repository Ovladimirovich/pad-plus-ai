#!/usr/bin/env python3
"""
🔍 Проверка, какая база данных используется в Render
"""

import sys
import os
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Проверка 1: Какая база используется локально
print("Проверка 1: Локальная конфигурация")
print("=" * 50)

try:
    from core.config_manager import get_database_url
    db_url = get_database_url()
    print(f"DATABASE_URL: {db_url[:50]}...")
    
    if db_url.startswith('postgresql'):
        print("Локально используется: PostgreSQL")
    elif db_url.startswith('sqlite'):
        print("Локально используется: SQLite")
    else:
        print(f"Локально используется: Неизвестно ({db_url[:20]}...)")
except Exception as e:
    print(f"Ошибка: {str(e)}")

# Проверка 2: Какая память используется локально
print("\nПроверка 2: Локальная память")
print("=" * 50)

try:
    from memory import get_episodic_memory, get_semantic_memory
    
    ep_mem = get_episodic_memory()
    sem_mem = get_semantic_memory()
    
    print(f"EpisodicMemory модуль: {type(ep_mem).__module__}")
    print(f"SemanticMemory модуль: {type(sem_mem).__module__}")
    
    if 'postgres' in type(ep_mem).__module__:
        print("Локально EpisodicMemory использует: PostgreSQL")
    else:
        print("Локально EpisodicMemory использует: SQLite")
        
    if 'postgres' in type(sem_mem).__module__:
        print("Локально SemanticMemory использует: PostgreSQL")
    else:
        print("Локально SemanticMemory использует: SQLite")
        
except Exception as e:
    print(f"Ошибка: {str(e)}")

# Проверка 3: Данные в локальной памяти
print("\nПроверка 3: Локальные данные")
print("=" * 50)

try:
    from memory import get_episodic_memory, get_semantic_memory
    
    ep_mem = get_episodic_memory()
    sem_mem = get_semantic_memory()
    
    ep_stats = ep_mem.get_stats()
    sem_stats = sem_mem.get_stats()
    
    print(f"Локальные эпизоды: {ep_stats.get('total_episodes', 0)}")
    print(f"Локальные знания: {sem_stats.get('total_knowledge', 0)}")
        
except Exception as e:
    print(f"Ошибка: {str(e)}")

# Проверка 4: Данные в Render
print("\nПроверка 4: Данные в Render")
print("=" * 50)

try:
    url = "https://pad-plus-ai-deploy.onrender.com/api/v1/memory/dashboard"
    response = requests.get(url, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        
        ep_count = data.get("episodic", {}).get("total_episodes", 0)
        sem_count = data.get("semantic", {}).get("total_knowledge", 0)
        
        print(f"Эпизоды в Render: {ep_count}")
        print(f"Знания в Render: {sem_count}")
        
        if ep_count == 0 and sem_count == 0:
            print("В Render данные не загружаются!")
            print("Возможные причины:")
            print("1. В Render используется SQLite вместо PostgreSQL")
            print("2. Проблема с подключением к Supabase в Render")
            print("3. Ошибка инициализации памяти в Render")
        else:
            print("В Render данные загружаются нормально")
    else:
        print(f"Ошибка получения данных: {response.status_code}")
        
except Exception as e:
    print(f"Ошибка: {str(e)}")

print("\n" + "=" * 50)
print("Вывод:")
print("=" * 50)

if ep_stats.get('total_episodes', 0) > 0 and ep_count == 0:
    print("1. Локально данные есть, в Render - нет")
    print("2. Это означает, что в Render используется другая база")
    print("3. Нужно проверить переменные окружения в Render")
    print("4. Убедиться, что DATABASE_URL правильно настроен в Render")