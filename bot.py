import os
import telebot
from telebot import types

# BOT_TOKEN задається як змінна середовища на хостингу (Railway)
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable BOT_TOKEN is not set. Please add it in your hosting settings.")

PAY_URL = os.getenv("PAY_URL")  # опціонально: посилання WayForPay

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💳 Абонементи")
    btn2 = types.KeyboardButton("🎁 Бонуси")
    btn3 = types.KeyboardButton("📊 Мій рівень")
    btn4 = types.KeyboardButton("💵 Оплатити онлайн")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def start(message):
    caption = (
        "<b>Вітаю у Fitness Club Parkova!</b>\n\n"
        "Це VIP Картка — знижки до 45% і бонуси.\n"
        "Обери дію нижче 👇"
    )
    if os.path.exists("logo.png"):
        try:
            with open("logo.png", "rb") as f:
                bot.send_photo(message.chat.id, f, caption=caption, reply_markup=main_menu())
                return
        except Exception:
            pass
    bot.send_message(message.chat.id, caption, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "💳 Абонементи")
def show_abonements(message):
    text = (
        "📉 <b>Рівні знижок за тривалість підписки</b>\n\n"
        "0–2 міс — <b>-20%</b>\n"
        "2–4 міс — <b>-25%</b>\n"
        "4–6 міс — <b>-30%</b>\n"
        "6–8 міс — <b>-35%</b>\n"
        "8–10 міс — <b>-40%</b>\n"
        "12+ міс — <b>-45%</b>\n"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🎁 Бонуси")
def show_bonuses(message):
    text = (
        "🎁 <b>Бонуси за рівнями</b>\n\n"
        "2-й рівень (2–4 міс): 2 чашки кави ☕☕\n"
        "3-й рівень (4–6 міс): кава ☕ + протеїновий коктейль 🥤 або предтренік\n"
        "4-й рівень (6–8 міс): кава ☕ + протеїновий коктейль 🥤 або предтренік\n"
        "5-й рівень (8–10 міс): протеїновий коктейль 🥤 + відвідування солярію 🌞\n"
        "6-й рівень (12+ міс): 2 кави ☕☕ + протеїновий коктейль 🥤 + відвідування солярію 🌞\n"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📊 Мій рівень")
def my_level(message):
    text = (
        "ℹ️ Відображення персонального рівня та абонемента\n"
        "зʼявиться після підключення CRM/таблиці. Поки що\n"
        "дивись загальні правила у розділі «Абонементи» та «Бонуси».")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💵 Оплатити онлайн")
def pay_online(message):
    if PAY_URL:
        bot.send_message(
            message.chat.id,
            f"💳 <b>Оплата підписки 100 грн/міс</b>\nНатисни посилання для оплати:\n{PAY_URL}"
        )
    else:
        bot.send_message(
            message.chat.id,
            "💳 Оплата онлайн скоро буде підключена.\n"
            "Надішли, будь ласка, посилання WayForPay адміністратору,\n"
            "або зачекай на оновлення меню."
        )

if __name__ == "__main__":
    print("✅ Бот запущено. Очікуємо повідомлення...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
