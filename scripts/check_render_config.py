#!/usr/bin/env python3
"""
🔍 Проверка конфигурации в Render
"""

import requests
import json

print("Проверка конфигурации в Render")
print("=" * 60)

# Проверка 1: Доступность сервиса
print("\n1. Проверка доступности сервиса...")
try:
    url = "https://pad-plus-ai-deploy.onrender.com"
    response = requests.get(url, timeout=10)
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        print("   Сервис доступен")
    else:
        print(f"   Сервис вернул код: {response.status_code}")
except Exception as e:
    print(f"   Ошибка: {str(e)}")

# Проверка 2: Проверка API
print("\n2. Проверка API endpoints...")
endpoints = [
    "/api/v1/status",
    "/api/v1/memory/stats",
    "/api/v1/memory/dashboard"
]

for endpoint in endpoints:
    try:
        url = f"https://pad-plus-ai-deploy.onrender.com{endpoint}"
        response = requests.get(url, timeout=15)
        print(f"   {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"   {endpoint}: Ошибка")

# Проверка 3: Проверка подключения к базе
print("\n3. Проверка подключения к базе...")
try:
    url = "https://pad-plus-ai-deploy.onrender.com/api/v1/memory/dashboard"
    response = requests.get(url, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        
        # Проверка данных
        episodic = data.get("episodic", {})
        semantic = data.get("semantic", {})
        
        print(f"   Эпизоды: {episodic.get('total_episodes', 0)}")
        print(f"   Знания: {semantic.get('total_knowledge', 0)}")
        
        if episodic.get('total_episodes', 0) == 0 and semantic.get('total_knowledge', 0) == 0:
            print("   Данные не загружаются")
            print("   Возможные причины:")
            print("   1. Неправильный DATABASE_URL в Render")
            print("   2. Проблема с подключением к базе")
            print("   3. Ошибка инициализации памяти")
        else:
            print("   Данные загружаются правильно")
    else:
        print(f"   Ошибка: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Ошибка: {str(e)}")

# Проверка 4: Рекомендации
print("\n" + "=" * 60)
print("Рекомендации:")
print("=" * 60)
print("1. Проверить переменные окружения в Render Dashboard")
print("2. Убедиться, что DATABASE_URL правильный:")
print("   postgresql://postgres.uixqufwbxefvkmhmausm:i8Edeq5rosD8sAeV@aws-1-eu-central-1.pooler.supabase.com:6543/postgres")
print("3. Проверить логи деплоя в Render")
print("4. Убедиться, что миграция прошла успешно")
print("5. Сделать редеплой, если нужно")

print("\n" + "=" * 60)
print("Дополнительная информация:")
print("=" * 60)
print("Если проблема не решена, нужно:")
print("1. Проверить настройки базы данных в Supabase")
print("2. Убедиться, что RLS правильно настроен")
print("3. Проверить подключение к базе из Render")
print("4. Проверить, что в базе есть данные")