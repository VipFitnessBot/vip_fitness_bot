import json
import os
from datetime import datetime, timedelta

import telebot
from telebot import types

from config import BOT_TOKEN

# ===  Ініціалізація  ===
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DATA_FILE = "users.json"

# === Збереження / завантаження ===
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_users()

# === Мапінг оплат -> рівень/знижка ===
def payments_to_level(payments: int) -> int:
    if payments <= 0:
        return 0
    if payments <= 2:
        return 1
    if payments <= 4:
        return 2
    if payments <= 6:
        return 3
    if payments <= 8:
        return 4
    if payments <= 10:
        return 5
    return 6

DISCOUNTS = {
    0: "0% (оплат ще не було)",
    1: "20%",
    2: "25%",
    3: "30%",
    4: "35%",
    5: "40%",
    6: "45%",
}

BONUSES = {
    2: "☕ 1 кава",
    3: "☕☕ 2 кави",
    4: "🥤 1 протеїновий коктейль",
    5: "☕ + 🥤 кава + протеїновий коктейль",
    6: "☕☕ + 🥤 2 кави + протеїновий коктейль",
}

# === Перевірка прострочки: якщо 3 дні без оплати — на 4-й день рівень падає до 0 ===
def enforce_expiry(user):
    last = user.get("last_payment")
    if not last:
        return user
    try:
        last_dt = datetime.fromisoformat(last)
    except Exception:
        return user
    if datetime.now() - last_dt > timedelta(days=3):
        user["payments"] = 0
        user["level"] = 0
        user["expired"] = True
    else:
        user["expired"] = False
    return user

# === Створення запису користувача, якщо немає ===
def ensure_user(user_id: int):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "payments": 0,
            "level": 0,
            "last_payment": None
        }
        save_users(users)
    users[uid] = enforce_expiry(users[uid])
    save_users(users)
    return users[uid]

# === Клавіатури ===
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Мій рівень", "🎁 Мої бонуси")
    kb.row("💳 Моя знижка", "🏆 Всі рівні")
    kb.row("💰 Оплатити підписку")
    return kb

def pay_inline_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔗 Оплатити (WayForPay)", url="https://secure.wayforpay.com/placeholder"))
    kb.add(types.InlineKeyboardButton(text="✅ Підтвердити оплату", callback_data="confirm_payment"))
    return kb

# === /start ===
@bot.message_handler(commands=["start"])
def cmd_start(message):
    user = ensure_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "👋 Вітаємо у VIP клубі! Обирай дію в меню нижче.",
        reply_markup=main_menu()
    )

# === Мій рівень ===
@bot.message_handler(func=lambda m: m.text == "📊 Мій рівень")
def my_level(message):
    user = ensure_user(message.from_user.id)
    level = user.get("level", 0)
    payments = user.get("payments", 0)
    discount = DISCOUNTS.get(level, "0%")
    bonus = BONUSES.get(level, "— бонусів на цьому рівні немає")
    expired_note = "⛔ Підписка прострочена: рівень скинуто до 0." if user.get("expired") else ""
    bot.send_message(
        message.chat.id,
        f"📊 <b>Ваш рівень:</b> {level}\n"
        f"💸 <b>Оплат:</b> {payments}\n"
        f"🎟 <b>Знижка:</b> {discount}\n"
        f"🎁 <b>Бонуси:</b> {bonus}\n\n"
        f"{expired_note}".strip()
    )

# === Моя знижка ===
@bot.message_handler(func=lambda m: m.text == "💳 Моя знижка")
def my_discount(message):
    user = ensure_user(message.from_user.id)
    level = user.get("level", 0)
    bot.send_message(message.chat.id, f"🎟 Ваша поточна знижка: <b>{DISCOUNTS.get(level, '0%')}</b>")

# === Мої бонуси ===
@bot.message_handler(func=lambda m: m.text == "🎁 Мої бонуси")
def my_bonuses(message):
    user = ensure_user(message.from_user.id)
    level = user.get("level", 0)
    bonus = BONUSES.get(level, "— бонусів на цьому рівні немає")
    bot.send_message(
        message.chat.id,
        f"🎁 Ваші бонуси: {bonus}\n\n"
        "ℹ️ Бонуси можна обміняти на інші товари у схожому ціновому діапазоні."
    )

# === Всі рівні (таблиця) ===
@bot.message_handler(func=lambda m: m.text == "🏆 Всі рівні")
def all_levels(message):
    lines = ["🏆 <b>Рівні, знижки, бонуси</b>"]
    for lvl in [0,1,2,3,4,5,6]:
        disc = DISCOUNTS.get(lvl, "—")
        bonus = BONUSES.get(lvl, "—")
        if lvl == 0:
            lines.append(f"Рівень 0: знижка {disc}, бонуси —")
        else:
            lines.append(f"Рівень {lvl}: знижка {disc}, бонуси: {bonus}")
    bot.send_message(message.chat.id, "\n".join(lines))

# === Оплата підписки (WayForPay заглушка + підтвердження) ===
@bot.message_handler(func=lambda m: m.text == "💰 Оплатити підписку")
def pay(message):
    ensure_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "💳 Оплата підписки 100 грн.\n"
        "Після успішної оплати натисніть кнопку нижче «✅ Підтвердити оплату».",
        reply_markup=pay_inline_kb()
    )

# Обробка підтвердження оплати (мануальна симуляція)
@bot.callback_query_handler(func=lambda c: c.data == "confirm_payment")
def confirm_payment(callback: types.CallbackQuery):
    uid = str(callback.from_user.id)
    user = ensure_user(callback.from_user.id)

    # +1 платіж
    user["payments"] = int(user.get("payments", 0)) + 1
    user["last_payment"] = datetime.now().isoformat()
    user["level"] = payments_to_level(user["payments"])
    user["expired"] = False
    users[uid] = user
    save_users(users)

    bot.answer_callback_query(callback.id, "Оплату підтверджено!")
    bot.edit_message_text(
        "✅ Оплату зараховано! Дякуємо 💙\n"
        f"Ваші нові параметри:\n"
        f"• Оплат: {user['payments']}\n"
        f"• Рівень: {user['level']}\n"
        f"• Знижка: {DISCOUNTS[user['level']]}",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )

# === Запуск ===
if __name__ == "__main__":
    print("🚀 VIP Fitness Bot запущено")
    bot.infinity_polling()
