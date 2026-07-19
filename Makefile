# Makefile для тестирования PAD+ AI

.PHONY: test test-unit test-integration test-coverage test-clean help
.PHONY: test-fast migrate migrate-check db-check precommit

# Все тесты
test:
	pytest -v

# Только unit тесты
test-unit:
	pytest tests/unit/ -v

# Только интеграционные тесты
test-integration:
	pytest tests/integration/ -v

# Тесты с покрытием
test-coverage:
	pytest --cov=backend --cov-report=html --cov-report=term-missing

# Быстрые тесты (без медленных)
test-fast:
	pytest -m "not slow" -v

# Новые критические тесты (app startup, migrations, auth, keys, docs)
test-core:
	pytest tests/test_app_startup.py tests/test_migrations.py tests/test_auth_flow.py tests/test_keys_endpoint.py tests/test_document_upload.py -v

# Тесты памяти
test-memory:
	pytest -m memory -v

# Тесты LLM
test-llm:
	pytest -m llm -v

# Тесты эмоций
test-emotion:
	pytest -m emotion -v

# Тесты знаний
test-knowledge:
	pytest -m knowledge -v

# Тесты автономии
test-autonomy:
	pytest -m autonomy -v

# API тесты (требуют запущенный сервер)
test-api:
	pytest -m api -v

# Миграции БД
migrate:
	python -m scripts.migrate

migrate-check:
	python -m scripts.migrate --check

# Проверка существования таблиц БД
db-check:
	python -c "from scripts.migrate import run_migrations; run_migrations(check=True)"

# Pre-commit проверка (быстрые тесты + миграции)
precommit: test-fast migrate-check

# Очистка кэша тестов
test-clean:
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Установка зависимостей
install:
	pip install -r requirements.txt

# Запуск сервера для API тестов
run-server:
	python backend/main.py

# Полная проверка (установка + тесты)
check: install test

# Smoke test (быстрая проверка проекта)
smoke:
	python scripts/smoke_test.py

# Миграция существующих трейсов в SQLite
migrate-traces:
	python scripts/migrate_traces.py

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  test          - Запустить все тесты"
	@echo "  test-unit     - Запустить только unit тесты"
	@echo "  test-integration - Запустить только интеграционные тесты"
	@echo "  test-coverage - Запустить тесты с покрытием"
	@echo "  test-fast     - Запустить быстрые тесты (без медленных)"
	@echo "  test-core     - Критические тесты (app startup, migrations, auth)"
	@echo "  test-memory   - Запустить тесты памяти"
	@echo "  test-llm      - Запустить тесты LLM"
	@echo "  test-emotion  - Запустить тесты эмоций"
	@echo "  test-knowledge - Запустить тесты знаний"
	@echo "  test-autonomy - Запустить тесты автономии"
	@echo "  test-api      - Запустить API тесты (требует сервер)"
	@echo "  migrate       - Применить миграции БД (Alembic upgrade head)"
	@echo "  migrate-check - Проверить статус миграций"
	@echo "  db-check      - Проверить существование таблиц"
	@echo "  precommit     - Pre-commit проверка (тесты + миграции)"
	@echo "  test-clean    - Очистить кэш тестов"
	@echo "  install       - Установить зависимости"
	@echo "  run-server    - Запустить сервер"
	@echo "  check         - Установить зависимости + запустить тесты"
	@echo "  smoke         - Smoke test (быстрая проверка проекта)"
	@echo "  migrate-traces- Миграция трейсов из JSON в SQLite"
	@echo "  help          - Показать эту справку"
