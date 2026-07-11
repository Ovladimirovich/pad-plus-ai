@echo off
echo Требует админ-прав. Запускай правой кнопкой -> "Run as administrator"
echo.

for %%S in (ArkaimCore ArkaimGateway) do (
    sc query "%%S" >nul 2>&1
    if errorlevel 1 (
        echo [%%S] не найден
    ) else (
        sc query "%%S" | find "RUNNING" >nul
        if not errorlevel 1 (
            echo [%%S] останавливаю...
            sc stop "%%S"
            timeout /t 2 /nobreak >nul
        ) else (
            echo [%%S] уже остановлен
        )
        sc config "%%S" start= disabled
        echo [%%S] тип запуска: Disabled
    )
    echo.
)

echo Проверка порта 8007:
netstat -ano | findstr ":8007 .*LISTEN"
if errorlevel 1 (
    echo Порт 8007 свободен
) else (
    echo Порт 8007 всё ещё занят (см. выше)
)

pause