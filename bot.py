import logging
import json
import os
import asyncio
import aiohttp
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIG ---
with open("token.txt", "r") as f:
    TOKEN = f.read().strip()

WFP_MERCHANT = os.getenv("WFP_MERCHANT", "your_merchant_account")
WFP_SECRET = os.getenv("WFP_SECRET", "your_secret_key")
WFP_URL = os.getenv("WFP_URL", "https://api.wayforpay.com/api/regularPayment")

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATA STORAGE ---
USERS_FILE = "users.json"

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- LEVELS ---
DISCOUNT_LEVELS = {
    1: "20% знижка на абонемент",
    2: "25% знижка на абонемент",
    3: "30% знижка на абонемент",
    4: "35% знижка на абонемент",
    5: "40% знижка на абонемент",
    6: "45% знижка на абонемент",
}

BONUS_LEVELS = {
    1: "--",
    2: "☕ Кава",
    3: "☕☕ Дві кави",
    4: "🥤 Протеїновий коктейль",
    5: "☕ + 🥤 Кава + протеїновий коктейль",
    6: "☕☕ + 🥤 Дві кави + протеїновий коктейль",
}

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {"level": 0, "payments": 0}
        save_users(users)
    keyboard = [[KeyboardButton("💳 Оплатити 100 грн")],
                [KeyboardButton("📊 Мій рівень")],
                [KeyboardButton("🎁 Бонуси та знижки")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Вітаю у VIP клубі! 🎉", reply_markup=reply_markup)

async def my_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    level = users.get(user_id, {}).get("level", 0)
    discount = DISCOUNT_LEVELS.get(level, "немає")
    bonus = BONUS_LEVELS.get(level, "немає")
    await update.message.reply_text(
        f"Ваш рівень: {level}\nЗнижка: {discount}\nБонус: {bonus}"
    )

async def bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎁 Рівні клубу:\n\n"
    for lvl in range(1, 7):
        text += f"{lvl}️⃣ - Знижка: {DISCOUNT_LEVELS[lvl]}, Бонус: {BONUS_LEVELS[lvl]}\n"
    await update.message.reply_text(text + "\nБонуси можна обміняти на інші товари у схожому ціновому діапазоні.")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()

    # Запит до WayForPay
    async with aiohttp.ClientSession() as session:
        data = {
            "merchantAccount": WFP_MERCHANT,
            "merchantDomainName": "vipclub.local",
            "orderReference": f"VIP_{user_id}_{users[user_id]['payments']+1}",
            "orderDate": int(asyncio.get_event_loop().time()),
            "amount": 100,
            "currency": "UAH",
            "productName": ["VIP Club"],
            "productPrice": [100],
            "productCount": [1],
            "clientEmail": "test@test.com"
        }
        async with session.post(WFP_URL, json=data) as resp:
            result = await resp.json()
            logger.info(result)
            if result.get("reasonCode") == 1100 or result.get("status") == "InProcessing":
                users[user_id]["payments"] += 1
                level = min(6, users[user_id]["payments"])
                users[user_id]["level"] = level
                save_users(users)
                await update.message.reply_text("✅ Оплата успішна! Ваш рівень оновлено.")
            else:
                await update.message.reply_text("❌ Помилка оплати. Спробуйте ще раз.")

# --- MAIN ---
async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("level", my_level))
    application.add_handler(CommandHandler("bonuses", bonuses))
    application.add_handler(CommandHandler("pay", pay))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
