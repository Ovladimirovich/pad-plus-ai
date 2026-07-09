#!/usr/bin/env python3
"""
🔍 Скрипт для проверки исправления в Render

Проверяет:
1. Доступность сервиса
2. Работу API endpoints с правильными данными
3. Отображение метрик памяти
"""

import requests
import json
import time
import sys

def check_service_availability():
    """Проверка доступности сервиса"""
    print("Проверка доступности сервиса...")
    
    url = "https://pad-plus-ai-deploy.onrender.com"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Сервис доступен")
            return True
        else:
            print(f"Сервис вернул код: {response.status_code}")
            return False
    except Exception as e:
        print(f"Ошибка подключения: {str(e)}")
        return False

def check_api_endpoints():
    """Проверка API endpoints"""
    print("\nПроверка API endpoints...")
    
    base_url = "https://pad-plus-ai-deploy.onrender.com"
    endpoints = [
        "/api/v1/status",
        "/api/v1/memory/stats",
        "/api/v1/knowledge/stats",
        "/api/v1/memory/dashboard"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                print(f"{endpoint}: {response.status_code}")
                
                # Проверка наличия данных
                if endpoint == "/api/v1/memory/dashboard":
                    if data.get("episodic", {}).get("total_episodes", 0) > 0:
                        print(f"   Эпизоды: {data['episodic']['total_episodes']}")
                    if data.get("semantic", {}).get("total_knowledge", 0) > 0:
                        print(f"   Знания: {data['semantic']['total_knowledge']}")
                
                results[endpoint] = {"status": "success", "data": data}
            else:
                print(f"{endpoint}: {response.status_code}")
                results[endpoint] = {"status": "error", "code": response.status_code}
                
        except Exception as e:
            print(f"{endpoint}: {str(e)}")
            results[endpoint] = {"status": "error", "error": str(e)}
    
    return results

def check_memory_stats():
    """Проверка статистики памяти"""
    print("\nПроверка статистики памяти...")
    
    url = "https://pad-plus-ai-deploy.onrender.com/api/v1/memory/dashboard"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверка эпизодической памяти
            episodic = data.get("episodic", {})
            total_episodes = episodic.get("total_episodes", 0)
            
            # Проверка семантической памяти
            semantic = data.get("semantic", {})
            total_knowledge = semantic.get("total_knowledge", 0)
            
            print(f"Эпизодическая память: {total_episodes} эпизодов")
            print(f"Семантическая память: {total_knowledge} знаний")
            
            if total_episodes > 0 and total_knowledge > 0:
                print("Метрики памяти работают корректно!")
                return True
            elif total_episodes == 0 and total_knowledge == 0:
                print("Метрики показывают 0 - возможно данные не загрузились")
                return False
            else:
                print("Частичные данные - некоторые метрики работают")
                return False
        else:
            print(f"Ошибка получения статистики: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Ошибка при проверке статистики: {str(e)}")
        return False

def main():
    """Главная функция проверки"""
    print("Проверка исправления в Render")
    print("=" * 60)
    
    # Шаг 1: Проверка доступности
    if not check_service_availability():
        print("\nСервис недоступен, проверка прервана")
        return 1
    
    # Шаг 2: Проверка API
    api_results = check_api_endpoints()
    
    # Шаг 3: Проверка метрик
    memory_ok = check_memory_stats()
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("Итоговый отчет:")
    print("=" * 60)
    
    if memory_ok:
        print("Исправление работает! Метрики памяти отображаются.")
        print("Проблема с Render решена!")
        return 0
    else:
        print("Проблема не решена. Метрики все еще не работают.")
        print("Проверьте:")
        print("1. Логи деплоя в Render Dashboard")
        print("2. Настройки DATABASE_URL")
        print("3. Подключение к Supabase")
        return 1

if __name__ == "__main__":
    sys.exit(main())