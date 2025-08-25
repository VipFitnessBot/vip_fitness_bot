import asyncio
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_TOKEN
from handlers import register_handlers


async def main():
    # створюємо бота
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # реєструємо всі хендлери
    register_handlers(app)

    # запускаємо
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Railway вже має активний event loop
            asyncio.ensure_future(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        # fallback на випадок проблем
        asyncio.run(main())
