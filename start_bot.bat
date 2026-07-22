@echo off
chcp 65001 >nul
title PAD+ AI Bot

cd /d "%~dp0"

if not exist ".env" (
    echo .env not found. Copy .env.example to .env and set BOT_TOKEN.
    pause
    exit /b 1
)

set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

:: Auto-install dependencies if missing
"%PY%" -c "import telegram" 2>nul
if errorlevel 1 (
    echo Installing python-telegram-bot...
    "%PY%" -m pip install -q python-telegram-bot 2>nul
    if errorlevel 1 (
        echo Failed to install. Run: pip install python-telegram-bot
        pause
        exit /b 1
    )
)

echo Starting PAD+ AI Telegram Bot (@padplusai_bot)...
echo.

start "PAD+ AI Bot" cmd /k ""%PY%" -m backend.bot.telegram_bot"

timeout /t 2 >nul
echo Bot starting in new window.
echo https://t.me/padplusai_bot
echo.
pause
