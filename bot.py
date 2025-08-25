import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_token():
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError("Файл token.txt не знайдено! Створи його і встав токен всередину.")

TOKEN = get_token()

users = {}

discount_levels = {
    1: 20,
    2: 25,
    3: 30,
    4: 35,
    5: 40,
    6: 45
}

bonus_levels = {
    1: "Кава",
    2: "2 кави",
    3: "Протеїновий коктейль",
    4: "Кава + протеїновий коктейль",
    5: "2 кави + протеїновий коктейль",
    6: "Максимальний пакет бонусів"
}

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {"level": 0, "payments": 0}
    keyboard = [["Мій рівень", "Знижки"], ["Бонуси", "Оплатити"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Вітаю у VIP-клубі! 🎉\nОбери дію:", reply_markup=reply_markup
    )

async def my_level(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    level = users.get(user_id, {"level": 0})["level"]
    await update.message.reply_text(f"Твій рівень: {level}")

async def discounts(update: Update, context: CallbackContext):
    text = "📉 Система знижок:\n"
    for lvl, disc in discount_levels.items():
        text += f"{lvl}-й рівень → {disc}%\n"
    await update.message.reply_text(text)

async def bonuses(update: Update, context: CallbackContext):
    text = "🎁 Система бонусів:\n"
    for lvl, bonus in bonus_levels.items():
        text += f"{lvl}-й рівень → {bonus}\n"
    text += "\nБонуси можна обміняти на інші товари в подібному ціновому діапазоні."
    await update.message.reply_text(text)

async def pay(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {"level": 0, "payments": 0}

    users[user_id]["payments"] += 1
    payments = users[user_id]["payments"]

    if payments >= 6:
        users[user_id]["level"] = 6
    else:
        users[user_id]["level"] = payments

    await update.message.reply_text(
        f"✅ Оплата прийнята!\nТепер твій рівень: {users[user_id]['level']}"
    )
# --- обробники команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вітаю у VIP-клубі! 🎉")

# --- Головний запуск ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # ⚡️ Використовуємо run_polling (він сам керує подіями, без asyncio.run)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
