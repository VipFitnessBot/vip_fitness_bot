import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словник користувачів {user_id: {"level": int, "last_payment": datetime, "payments": int}}
users = {}

# Бонуси за рівнями
BONUSES = {
    2: "Кава",
    3: "2 кави",
    4: "Протеїновий коктейль",
    5: "Кава + протеїновий коктейль",
    6: "2 кави + протеїновий коктейль"
}

# Знижки
DISCOUNTS = {
    1: "20%",
    2: "20%",
    3: "25%",
    4: "25%",
    5: "30%",
    6: "30%",
    7: "35%",
    8: "40%",
    9: "45%"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {"level": 0, "last_payment": None, "payments": 0}

    keyboard = [
        [InlineKeyboardButton("💳 Оплатити 100 грн (VIP)", callback_data="pay")],
        [InlineKeyboardButton("🎁 Мої бонуси", callback_data="bonus")],
        [InlineKeyboardButton("📉 Мої знижки", callback_data="discount")],
        [InlineKeyboardButton("📊 Мій рівень", callback_data="level")],
        [InlineKeyboardButton("ℹ️ Усі можливості клубу", callback_data="all_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Вітаю у VIP клубі! Обери опцію:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in users:
        users[user_id] = {"level": 0, "last_payment": None, "payments": 0}

    data = query.data
    if data == "pay":
        users[user_id]["payments"] += 1
        users[user_id]["last_payment"] = datetime.datetime.now()
        users[user_id]["level"] = min(users[user_id]["payments"], 9)
        await query.edit_message_text("✅ Оплата пройшла успішно (заглушка). Рівень оновлено!")

    elif data == "bonus":
        level = users[user_id]["level"]
        bonuses = [f"{lvl} рівень → {BONUSES[lvl]}" for lvl in BONUSES]
        current = BONUSES.get(level, "Ще немає бонусів")
        await query.edit_message_text(f"🎁 Твої бонуси: {current}\n\nМожливі:\n" + "\n".join(bonuses))

    elif data == "discount":
        level = users[user_id]["level"]
        current = DISCOUNTS.get(level, "Немає знижки")
        all_discounts = [f"{lvl} рівень → {DISCOUNTS[lvl]}" for lvl in DISCOUNTS]
        await query.edit_message_text(f"📉 Твоя знижка: {current}\n\nМожливі:\n" + "\n".join(all_discounts))

    elif data == "level":
        level = users[user_id]["level"]
        await query.edit_message_text(f"📊 Твій рівень: {level}")

    elif data == "all_info":
        bonuses = "\n".join([f"{lvl} рівень → {BONUSES[lvl]}" for lvl in BONUSES])
        discounts = "\n".join([f"{lvl} рівень → {DISCOUNTS[lvl]}" for lvl in DISCOUNTS])
        await query.edit_message_text(f"🎁 Бонуси:\n{bonuses}\n\n📉 Знижки:\n{discounts}")

# Запуск
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
