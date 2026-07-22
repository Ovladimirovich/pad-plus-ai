@echo off
chcp 65001 >nul
title PAD+ AI Bot - Telegram

echo ============================================
echo   PAD+ AI v4.1 - Telegram Bot
echo ============================================
echo.

:: Активация venv если существует
if exist "venv\Scripts\activate.bat" (
    echo [1/3] Активация виртуального окружения...
    call venv\Scripts\activate
    echo   ✓ venv активирован
    echo.
) else (
    echo ⚠ venv не найден! Запуск без виртуального окружения.
    echo   Для создания: python -m venv venv
    echo.
)

:: Проверяем наличие .env
if not exist ".env" (
    echo ⚠ .env не найден! Создайте .env из .env.example
    echo   Пример: copy .env.example .env
    echo.
)

:: Проверяем наличие BOT_TOKEN
python -c "from dotenv import load_dotenv; import os; load_dotenv(); t = os.getenv('BOT_TOKEN'); exit(0 if t and t != 'your_telegram_bot_token' else 1)" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ BOT_TOKEN не настроен! Укажите токен в .env
    echo   Пример: BOT_TOKEN=ваш_токен_от_BotFather
    echo.
)

:: Запускаем бота
echo [2/3] Запуск Telegram бота...
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    start "PAD+ AI Bot" cmd /k "echo Telegram bot @padplusai_bot запускается... && "%PYTHON_EXE%" -m backend.bot.telegram_bot"
) else (
    start "PAD+ AI Bot" cmd /k "echo Telegram bot @padplusai_bot запускается... && python -m backend.bot.telegram_bot"
)

echo   ✓ Бот запускается...
echo.

:: Небольшая пауза
timeout /t 3 >nul

echo ============================================
echo   ✓ PAD+ AI Bot запущен!
echo ============================================
echo.
echo   Бот:     https://t.me/padplusai_bot
echo   Канал:   https://t.me/padplusai
echo   Чат:     https://t.me/padplusai_chat
echo.
echo   Для остановки закройте окно бота
echo   или выполните: taskkill /FI "WINDOWTITLE eq PAD+ AI Bot"
echo.
pause
