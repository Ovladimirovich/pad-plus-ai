# WORKFLOW — Локальная разработка → GitHub → Render

## Общая схема

```
[Локальная машина (OpenCode)]
        │
        │ 1. Коммити изменения
        ▼
[GIT HUB — main branch]
        │
        │ 2. Auto-deploy (Render)
        ▼
[RENDER — pad-plus-ai.onrender.com]
```

**Правило золотое:** пушить в GitHub — только протестированные изменения.

---

## Этап 1: Локальная разработка

### Начало работы
```powershell
# Pull последние изменения
cd "C:\пад ал датабаз а  чистый\PAD+ AI чистый"
git pull origin main

# Убедиться что venv активен
venv\Scripts\activate
```

### Сделать изменения
- Редактировать файлы
- Добавлять новые файлы
- Тестировать локально

---

## Этап 2: Локальное тестирование

### Быстрый тест бэкенда
```powershell
cd backend
uvicorn main:app --reload --port 8007
```
Открыть: http://localhost:8007/docs — проверить что Swagger работает.

### Быстрый тест фронтенда
```powershell
cd frontend
npm run dev
```
Открыть: http://localhost:5174

### Полный стек (аналог start.bat без запуска демо)
```powershell
.\start.bat
```

### Проверка критических функциональностей
1. http://localhost:8007/health — backend отвечает
2. http://localhost:5174 — фронтенд грузится
3. Чат работает → отправить сообщение
4. X-Ray → проверить что трасса видна
5. Research Platform → проверить что работает

### Критически важно перед пушем
- [ ] Backend стартует без ошибок
- [ ] Frontend грузится
- [ ] Базовая функциональность (чат, X-Ray) работает
- [ ] Новые изменения не сломали существующее

---

## Этап 3: Коммит и пуш в GitHub

### Только после успешного локального теста
```powershell
git add .
git commit -m "описание изменений"
git push origin main
```

### Что NOT делать
- ❌ Пушить непротестированные изменения
- ❌ Пушить сломанный код "потом починю на Render"
- ❌ Пушить изменения если локальный тест не пройден

---

## Этап 4: Render авто-деплой

После `git push origin main`:
1. Render детектит изменения
2. Авто-собирает и деплоит
3. Демо обновляется на `pad-plus-ai.onrender.com`

### Проверка после деплоя
- [ ] https://pad-plus-ai.onrender.com открывается
- [ ] Health endpoint работает
- [ ] Основная функциональность доступна

---

## MonkeyCode

MonkeyCode работает через GitHub в браузере. Синхронизация:
1. Ветка `main` — единственная рабочая ветка
2. MonkeyCode создаёт `monkeycode/<task>` для работы
3. Готовое мержится в `main` через коммит в `main`
4. Оба инструмента читают `AGENTS.md` и `.monkeycode.md`

### Протокол переключения
1. Перед сменой инструмента — закоммити и push
2. В начале работы — pull первым делом
3. Тестируй локально перед пушем
4. Описывай задачи в коммитах

---

## Ключевые ссылки

| Ресурс | URL |
|--------|-----|
| GitHub | https://github.com/Ovladimirovich/pad-plus-ai |
| Render Demo | https://pad-plus-ai.onrender.com |
| Swagger | http://localhost:8007/docs (локально) |
| Telegram Bot | https://t.me/padplusai_bot |
| Telegram Channel | https://t.me/padplusai |
| Telegram Chat | https://t.me/padplusai_chat |