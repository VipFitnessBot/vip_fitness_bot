import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Завантаження токена з файлу
with open("token.txt") as f:
    BOT_TOKEN = f.read().strip()

# Зберігання даних користувачів
users = {}

# Конфіг рівнів знижок і бонусів
DISCOUNTS = {
    1: "20%",
    2: "25%",
    3: "30%",
    4: "35%",
    5: "40%",
    6: "45%",
}

BONUSES = {
    1: "☕ Кава",
    2: "☕☕ Дві кави",
    3: "🥤 Протеїновий коктейль",
    4: "☕ + 🥤 Кава + протеїновий коктейль",
    5: "☕☕ + 🥤 Дві кави + протеїновий коктейль",
    6: "🎁 Максимальний набір бонусів",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартове меню"""
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {"level": 0, "payments": 0}

    keyboard = [
        [InlineKeyboardButton("💳 Оплатити VIP (100 грн)", callback_data="pay")],
        [InlineKeyboardButton("📊 Мій рівень", callback_data="profile")],
        [InlineKeyboardButton("🎁 Усі бонуси і знижки", callback_data="all_rewards")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Ласкаво просимо у VIP клуб!\n\n"
        "Тут ви можете оплатити підписку, переглянути свій рівень і бонуси.",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка кнопок"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "pay":
        await handle_payment(query, user_id)
    elif query.data == "profile":
        await show_profile(query, user_id)
    elif query.data == "all_rewards":
        await show_all_rewards(query)


async def handle_payment(query, user_id):
    """Оплата (зараз заглушка)"""
    if user_id not in users:
        users[user_id] = {"level": 0, "payments": 0}

    users[user_id]["payments"] += 1

    # Розрахунок рівня
    payments = users[user_id]["payments"]
    if payments == 1:
        users[user_id]["level"] = 1
    elif payments == 2:
        users[user_id]["level"] = 1
    elif payments == 3:
        users[user_id]["level"] = 2
    elif payments == 4:
        users[user_id]["level"] = 3
    elif payments == 5:
        users[user_id]["level"] = 4
    elif payments == 6:
        users[user_id]["level"] = 5
    elif payments >= 7:
        users[user_id]["level"] = 6

    await query.edit_message_text(
        "✅ Оплата успішна (зараз тестовий режим WayForPay)\n\n"
        "Ваш рівень оновлено!"
    )


async def show_profile(query, user_id):
    """Показати профіль"""
    level = users[user_id]["level"]
    discount = DISCOUNTS.get(level, "0%")
    bonus = BONUSES.get(level, "—")

    text = (
        f"👤 Ваш профіль\n\n"
        f"📊 Рівень: {level}\n"
        f"💸 Знижка: {discount}\n"
        f"🎁 Бонус: {bonus}\n\n"
        f"ℹ️ Бонуси можна обміняти на інші товари "
        f"у схожому ціновому діапазоні."
    )

    await query.edit_message_text(text)


async def show_all_rewards(query):
    """Показати всі рівні і нагороди"""
    text = "📊 Усі рівні VIP клубу:\n\n"
    for lvl in range(1, 7):
        text += (
            f"⭐ Рівень {lvl}: "
            f"{DISCOUNTS[lvl]} + {BONUSES[lvl]}\n"
        )

    await query.edit_message_text(text)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Без asyncio.run(), запускаємо напряму
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
