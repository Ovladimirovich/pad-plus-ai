@echo off
chcp 65001 >nul
title PAD+ AI - Остановка системы

echo ============================================
echo   PAD+ AI v4.0 - Остановка системы...
echo ============================================
echo.

:: Находим и останавливаем процессы по PID
echo [1/3] Остановка Backend (порт 8080)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    echo   - Найден процесс PID %%a, останавливаем...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo     ✗ Не удалось остановить процесс
    ) else (
        echo     ✓ Процесс остановлен
    )
)

echo.
echo [2/3] Остановка Frontend (порт 5174)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5174 ^| findstr LISTENING') do (
    echo   - Найден процесс PID %%a, останавливаем...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo     ✗ Не удалось остановить процесс
    ) else (
        echo     ✓ Процесс остановлен
    )
)

:: Останавливаем только наши процессы (по окнам)
echo.
echo [3/3] Остановка окон с нашими процессами...
taskkill /F /FI "WINDOWTITLE eq PAD+ AI Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq PAD+ AI Frontend*" >nul 2>&1

:: Если окна не закрылись — по портам (безопасно)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5174 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo   ✓ Все процессы остановлены

timeout /t 2 >nul

:: Проверяем что порты свободны
echo.
echo ============================================
echo   Проверка освобождения портов:
echo ============================================

set PORTS_FREE=1

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    echo   ✗ Порт 8080 всё ещё занят (PID %%a)
    set PORTS_FREE=0
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5174 ^| findstr LISTENING') do (
    echo   ✗ Порт 5174 всё ещё занят (PID %%a)
    set PORTS_FREE=0
)

if "%PORTS_FREE%"=="1" (
    echo   ✓ Порт 8080 - свободен
    echo   ✓ Порт 5174 - свободен
    echo.
    echo ============================================
    echo   ✓ Система PAD+ AI полностью остановлена!
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   ⚠ Некоторые процессы всё ещё активны
    echo   Попробуйте перезагрузить компьютер
    echo ============================================
)

echo.
pause