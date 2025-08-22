import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

# Словник користувачів {id: {"level": int, "active": bool}}
users = {}

# Опис бонусів
bonuses = {
    2: "☕ 1 кава (можна обміняти)",
    3: "☕☕ 2 кави (можна обміняти)",
    4: "🥤 Протеїновий коктейль (можна обміняти)",
    5: "☕ + 🥤 кава і протеїновий коктейль (можна обміняти)",
    6: "☕☕ + 🥤 2 кави і протеїновий коктейль (можна обміняти)",
}

discounts = {
    1: "0-2 місяці ➝ -20%",
    2: "2-4 місяці ➝ -25%",
    3: "4-6 місяців ➝ -30%",
    4: "6-8 місяців ➝ -35%",
    5: "8-10 місяців ➝ -40%",
    6: "12+ місяців ➝ -45%",
}

# Стартова команда
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {"level": 1, "active": True}
    bot.send_message(user_id, "👋 Вітаю у VIP Fitness Club!
"
                              "Ви отримуєте знижки та бонуси за підписку.
"
                              "Використовуйте меню нижче.")

# Меню
@bot.message_handler(commands=["menu"])
def menu(message):
    user_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💳 Мій рівень", "🎁 Бонуси")
    markup.add("📉 Знижки", "💰 Оплатити підписку")
    bot.send_message(user_id, "Оберіть опцію:", reply_markup=markup)

# Мій рівень
@bot.message_handler(func=lambda m: m.text == "💳 Мій рівень")
def my_level(message):
    user_id = message.chat.id
    level = users[user_id]["level"]
    bot.send_message(user_id, f"Ваш рівень: {level}
Знижка: {discounts.get(level, 'Немає')}")

# Бонуси
@bot.message_handler(func=lambda m: m.text == "🎁 Бонуси")
def my_bonuses(message):
    user_id = message.chat.id
    level = users[user_id]["level"]
    text = bonuses.get(level, "Бонусів поки немає.")
    bot.send_message(user_id, f"Ваші бонуси: {text}")

# Знижки
@bot.message_handler(func=lambda m: m.text == "📉 Знижки")
def discount_list(message):
    text = "📉 Система знижок:

"
    for k, v in discounts.items():
        text += f"{v}
"
    bot.send_message(message.chat.id, text)

# Оплата (заглушка WayForPay)
@bot.message_handler(func=lambda m: m.text == "💰 Оплатити підписку")
def pay(message):
    bot.send_message(message.chat.id, "💳 Оплата через WayForPay поки у розробці.
"
                                      "Тут буде кнопка для онлайн-оплати.")

print("Бот запущено...")
bot.polling(none_stop=True)
