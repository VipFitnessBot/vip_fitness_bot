import telebot
from telebot import types
import datetime

# 🔑 Токен вставляєш СЮДИ (в лапках!)
BOT_TOKEN = "7717901847:AAHytaN_hObl-6G8IB43r8qhRSZ7svnO6gM"
bot = telebot.TeleBot(BOT_TOKEN)

# 🗂 Тут буде зберігатися інформація про користувачів (для тесту — у пам'яті)
users = {}

# 📊 Знижки по рівнях
discounts = {
    1: "20%",
    2: "25%",
    3: "30%",
    4: "35%",
    5: "40%",
    6: "45%"
}

# 🎁 Бонуси по рівнях
bonuses = {
    2: "☕️ 1 кава",
    3: "☕️ 2 кави",
    4: "🥤 1 протеїновий коктейль",
    5: "☕️ 1 кава + 🥤 протеїновий коктейль",
    6: "☕️ 2 кави + 🥤 протеїновий коктейль"
}

# 🏁 Команда старт
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {
            "months": 0,
            "start_date": datetime.date.today()
        }

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎟 Моя знижка")
    btn2 = types.KeyboardButton("🎁 Мої бонуси")
    btn3 = types.KeyboardButton("📊 Мій рівень")
    btn4 = types.KeyboardButton("💳 Оплата підписки")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)

    bot.send_message(
        user_id,
        "👋 Вітаю у VIP клубі!\nТут ти можеш дізнатися про свої знижки, бонуси та оплачувати підписку.",
        reply_markup=markup
    )

# 📉 Знижка
@bot.message_handler(func=lambda m: m.text == "🎟 Моя знижка")
def my_discount(message):
    user_id = message.chat.id
    level = get_level(users[user_id]["months"])
    discount = discounts.get(level, "0%")
    bot.send_message(user_id, f"Твоя знижка: {discount}")

# 🎁 Бонуси
@bot.message_handler(func=lambda m: m.text == "🎁 Мої бонуси")
def my_bonuses(message):
    user_id = message.chat.id
    level = get_level(users[user_id]["months"])
    bonus = bonuses.get(level, "Немає бонусів на цьому рівні")
    bot.send_message(user_id, f"Твої бонуси: {bonus}\n\n👉 Бонуси можна обміняти на інші товари схожої вартості.")

# 📊 Рівень
@bot.message_handler(func=lambda m: m.text == "📊 Мій рівень")
def my_level(message):
    user_id = message.chat.id
    level = get_level(users[user_id]["months"])
    bot.send_message(user_id, f"Твій рівень: {level}️⃣\nОплачено місяців: {users[user_id]['months']}")

# 💳 Оплата підписки
@bot.message_handler(func=lambda m: m.text == "💳 Оплата підписки")
def pay_subscription(message):
    user_id = message.chat.id
    # 👇 Заглушка WayForPay
    bot.send_message(user_id, "💳 Оплата доступна за посиланням:\n👉 [ТУТ БУДЕ WAYFORPAY]")

    # Для тесту можна імітувати оплату
    users[user_id]["months"] += 1
    bot.send_message(user_id, f"✅ Оплата зарахована! Тепер у тебе {users[user_id]['months']} місяців підписки.")

# 📏 Функція визначення рівня
def get_level(months):
    if months < 2:
        return 1
    elif months < 4:
        return 2
    elif months < 6:
        return 3
    elif months < 8:
        return 4
    elif months < 10:
        return 5
    else:
        return 6

# ▶️ Запуск
bot.polling(none_stop=True)