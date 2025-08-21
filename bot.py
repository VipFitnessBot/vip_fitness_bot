import telebot

# 🚨 Сюди встав свій токен прямо в лапках:
BOT_TOKEN = "7717901847:AAHytaN_hob1-6G8IB43r8qhRSZ7svnO6gM"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Вітаю у VIP Fitness Bot!")

if name == "__main__":
    print("Бот запущено...")
    bot.infinity_polling()