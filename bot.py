import os
import telebot

# Діагностика: виведемо всі змінні оточення
print("🔍 Усі змінні оточення:")
for key, value in os.environ.items():
    if "TOKEN" in key:  # тільки ті, що пов'язані з токенами
        print(f"{key} = {value}")

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Не знайдено токен! Додай змінну BOT_TOKEN у Railway.")

print(f"✅ BOT_TOKEN успішно зчитано: {BOT_TOKEN[:10]}...")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "👋 Привіт! Бот працює.")

print("🚀 Бот запущено...")
bot.polling(none_stop=True)