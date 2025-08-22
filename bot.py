import telebot
import json
import os

# === Налаштування ===
BOT_TOKEN = "7717901847:AAHytaN_hObl-6G8IB43r8qhRSZ7svnO6gM"  # ВСТАВ СЮДИ СВІЙ ТОКЕН
ADMIN_ID = 430950918  # твій Telegram ID
DATA_FILE = "users.json"

# === Ініціалізація ===
bot = telebot.TeleBot(BOT_TOKEN)

# === Завантаження даних ===
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# === Збереження даних ===
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

users = load_data()

# === Отримати рівень користувача ===
def get_level(user_id):
    return users.get(str(user_id), 1)

# === Встановити рівень ===
def set_level(user_id, level):
    users[str(user_id)] = level
    save_data(users)

# === Текст бонусів ===
def get_bonus_text(level):
    bonuses = {
        2: "☕ Кава",
        3: "☕☕ Дві кави",
        4: "🥤 Протеїновий коктейль",
        5: "☕ + 🥤 Кава + протеїновий коктейль",
        6: "☕☕ + 🥤 Дві кави + протеїновий коктейль"
    }
    return bonuses.get(level, "Поки бонусів немає 🙂") + "\nБонуси можна обміняти на інші товари у схожому ціновому діапазоні."

# === Команда старт ===
@bot.message_handler(commands=["start"])
def start(message):
    level = get_level(message.from_user.id)
    text = f"Привіт, {message.from_user.first_name}!\nТвій рівень у VIP клубі: {level}\n{get_bonus_text(level)}"
    bot.send_message(message.chat.id, text)

# === Команда перевірки рівня ===
@bot.message_handler(commands=["myvip"])
def my_vip(message):
    level = get_level(message.from_user.id)
    text = f"Твій рівень: {level}\n{get_bonus_text(level)}"
    bot.send_message(message.chat.id, text)

# === Адмін: встановити рівень ===
@bot.message_handler(commands=["setlevel"])
def setlevel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ У вас немає доступу до цієї команди.")
        return

    try:
        _, user_id, level = message.text.split()
        user_id = int(user_id)
        level = int(level)
        set_level(user_id, level)
        bot.send_message(message.chat.id, f"✅ Рівень {level} встановлено користувачу {user_id}")
    except:
        bot.send_message(message.chat.id, "❌ Формат: /setlevel USER_ID LEVEL")

print("Бот запущений...")
bot.infinity_polling()
