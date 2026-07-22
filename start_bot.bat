@echo off
chcp 65001 >nul
title PAD+ AI Bot

cd /d "%~dp0"

if not exist ".env" (
    echo .env not found. Copy .env.example to .env and set BOT_TOKEN.
    pause
    exit /b 1
)

echo Starting PAD+ AI Telegram Bot (@padplusai_bot)...
echo.

if exist "venv\Scripts\python.exe" (
    start "PAD+ AI Bot" cmd /k "venv\Scripts\python.exe -m backend.bot.telegram_bot"
) else (
    start "PAD+ AI Bot" cmd /k "python -m backend.bot.telegram_bot"
)

timeout /t 2 >nul
echo Bot starting in new window.
echo https://t.me/padplusai_bot
echo.
pause
