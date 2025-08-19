import telebot
import os

# Отримуємо токен з змінної середовища (безпечніше ніж вписувати у коді)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ Не знайдено токен! Додай змінну BOT_TOKEN у Railway.")

bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Привіт! Бот працює.")

# Тестове меню з кнопками
@bot.message_handler(commands=['menu'])
def menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("📅 Абонементи")
    btn2 = telebot.types.KeyboardButton("🎁 Бонуси")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Оберіть опцію:", reply_markup=markup)

# Обробка натискання кнопок
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    if message.text == "📅 Абонементи":
        bot.reply_to(message, "Тут буде інформація про абонементи.")
    elif message.text == "🎁 Бонуси":
        bot.reply_to(message, "Тут буде інформація про бонуси.")
    else:
        bot.reply_to(message, "Я поки що не знаю цієї команди 🙂")

print("🚀 Бот запущено!")
bot.infinity_polling()