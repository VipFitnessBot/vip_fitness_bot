import logging
import os
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Читаємо токен з token.txt
with open("token.txt", "r") as f:
    TOKEN = f.read().strip()

# Конфіг з WayForPay (змінні Railway)
WFP_MERCHANT = os.getenv("WFP_MERCHANT")
WFP_SECRET = os.getenv("WFP_SECRET")
WFP_DOMAIN = os.getenv("WFP_DOMAIN", "https://secure.wayforpay.com/pay")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Доступні рівні
DISCOUNTS = {
    1: 20,
    2: 25,
    3: 30,
    4: 35,
    5: 40,
    6: 45
}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Оформити підписку", callback_data="subscribe")]
    ]
    await update.message.reply_text(
        "Вітаю! Тут ви можете оформити підписку.", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обробка натискань
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "subscribe":
        keyboard = [
            [InlineKeyboardButton(f"Рівень {lvl} - знижка {disc}%", callback_data=f"pay_{lvl}")]
            for lvl, disc in DISCOUNTS.items()
        ]
        await query.edit_message_text(
            text="Оберіть рівень підписки:", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("pay_"):
        lvl = int(query.data.split("_")[1])
        amount = 1000  # умовна ціна
        discount = DISCOUNTS[lvl]
        final_price = amount * (100 - discount) // 100

        payment_url = f"{WFP_DOMAIN}?merchantAccount={WFP_MERCHANT}&amount={final_price}&orderReference=test_{lvl}&merchantDomainName={WFP_MERCHANT}&currency=UAH&productName=VIP&productCount=1&productPrice={final_price}"

        await query.edit_message_text(
            text=f"Оплата рівня {lvl} зі знижкою {discount}%.
Сума: {final_price} грн.
[Оплатити]({payment_url})",
            parse_mode="Markdown"
        )

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # 🟢 Без проблем з event loop
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
