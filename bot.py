import os
import telebot

# Отримуємо токен із змінних середовища (Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Не знайдено токен! Додай змінну BOT_TOKEN у Railway.")

bot = telebot.TeleBot(BOT_TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "✅ Бот запущений і працює на Railway!")

# Команда /help
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "ℹ️ Доступні команди:\n/start - перевірка роботи\n/help - список команд")

print("🚀 Бот стартує...")

bot.polling(none_stop=True)
