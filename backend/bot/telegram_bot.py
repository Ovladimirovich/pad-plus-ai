import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

# Load .env from project root or current dir
for dotenv_path in [Path(__file__).parent.parent.parent / ".env", Path.cwd() / ".env"]:
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        logger.info("Loaded environment from %s", dotenv_path)
        break

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_ENABLED = bool(BOT_TOKEN) and BOT_TOKEN != "your_telegram_bot_token"

COMMANDS = [
    BotCommand("start", "Приветствие и информация о проекте"),
    BotCommand("microscope", "AI Under Microscope — визуализация пайплайна"),
    BotCommand("xray", "X-Ray — наблюдаемость AI-систем"),
    BotCommand("pipeline", "25 фаз когнитивного пайплайна"),
    BotCommand("article1", "Первая статья на dev.to"),
    BotCommand("article2", "Вторая статья на dev.to"),
    BotCommand("github", "Ссылка на GitHub репозиторий"),
    BotCommand("demo", "Живое демо на Render"),
    BotCommand("channel", "Канал @padplusai"),
    BotCommand("feedback", "Связаться с автором"),
    BotCommand("chat", "Чат-группа для обсуждения проекта"),
]

WELCOME_TEXT = """
👋 Привет! Я бот проекта PAD+ AI.

PAD+ AI — это open-source исследовательская платформа для создания когнитивных архитектур поверх языковых моделей.

Что я умею:
🔬 /microscope — как работает AI Under Microscope
📡 /xray — что такое X-Ray наблюдаемость
📖 /article1 — первая статья (Eng)
📖 /article2 — вторая статья (Eng)
💬 /chat — чат-группа проекта
🐙 /github — ссылка на репозиторий
🌐 /demo — живое демо на Render
📢 /channel — наш канал @padplusai
💬 /feedback — связаться с автором

PAD+ AI проводит запрос через 25 когнитивных фаз: от определения направленности мышления до верификации утверждений.

Open Source · Apache 2.0
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_TEXT.strip())


async def cmd_microscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🔬 AI Under Microscope — визуализация всех 25 фаз pipeline в реальном времени.\n\n"
        "Каждая фаза показывает иконку категории, статус (pending/running/done/error), "
        "оценку Why-card и длительность выполнения.\n\n"
        "Данные приходят через WebSocket /api/v1/xray/ws с fallback на polling.\n"
        "Доступно на странице #research в интерфейсе PAD+ AI."
    )
    await update.message.reply_text(text)


async def cmd_xray(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📡 X-Ray — система наблюдаемости для AI-пайплайнов.\n\n"
        "Каждый запрос становится Trace. Внутри — Span'ы (фазы). "
        "В отличие от логов, X-Ray сохраняет структуру выполнения: "
        "причинно-следственные связи, время каждой фазы, аудит целостности.\n\n"
        "Режимы: live / shadow / readonly / disabled.\n"
        "Персистентность на диск, авто-восстановление после перезапуска."
    )
    await update.message.reply_text(text)


async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🧬 25 фаз когнитивного пайплайна PAD+ AI:\n\n"
        "Sync path:\n"
        "anti_loop → safety → intent → rag → knowledge_graph → episodic → "
        "semantic → emotion → impulse → persona → roots → identity → "
        "generate → truth_loop → evaluation → save_episode → extraction → "
        "emotion_update → impulse_update → events_broadcast → response_guard\n\n"
        "Background (fire-and-forget):\n"
        "consolidation, procedure_success, persona_evolution, health, "
        "reflection, dreams, metrics"
    )
    await update.message.reply_text(text)


async def cmd_article1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 Первая статья: Building a modular cognitive architecture\n"
        "https://dev.to/_a9de0f38ed294cfb7e5e/building-a-modular-cognitive-architecture-around-modern-language-models-2lc1"
    )


async def cmd_article2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 Вторая статья: X-Ray for AI\n"
        "https://dev.to/_a9de0f38ed294cfb7e5e/x-ray-for-ai-or-how-i-stopped-understanding-my-own-neural-network-and-built-my-own-apm-2l4p"
    )


async def cmd_github(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🐙 GitHub: github.com/Ovladimirovich/pad-plus-ai\n"
        "Звёзды и PR приветствуются!"
    )


async def cmd_demo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🌐 Живое демо: pad-plus-ai.onrender.com\n"
        "Работает на Render. Каждый запрос оставляет полную X-Ray трассу."
    )


async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📢 Наш канал: @padplusai\n"
        "Релизы, devlog, статьи, open source."
    )


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💬 PAD+ AI Chat — сообщество для обсуждения проекта.\n\n"
        "Ссылка: https://t.me/padplusai_chat\n\n"
        "Обсуждаем архитектуру, фичи, баги, идеи. "
        "Сюда можно прийти с вопросом или предложением."
    )


async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💬 По вопросам и предложениям — @Ovladimirovich\n"
        "Или откройте Issue на GitHub: github.com/Ovladimirovich/pad-plus-ai/issues"
    )


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("microscope", cmd_microscope))
    app.add_handler(CommandHandler("xray", cmd_xray))
    app.add_handler(CommandHandler("pipeline", cmd_pipeline))
    app.add_handler(CommandHandler("article1", cmd_article1))
    app.add_handler(CommandHandler("article2", cmd_article2))
    app.add_handler(CommandHandler("github", cmd_github))
    app.add_handler(CommandHandler("demo", cmd_demo))
    app.add_handler(CommandHandler("channel", cmd_channel))
    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_handler(CommandHandler("feedback", cmd_feedback))

    return app


def main() -> None:
    if not BOT_ENABLED:
        logger.warning("BOT_TOKEN not configured. Bot is disabled.")
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = build_application()
    logger.info("Starting PAD+ AI Telegram bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
