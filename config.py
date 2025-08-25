import os

# === Telegram token з token.txt ===
def load_token():
    try:
        with open("token.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError("Файл token.txt не знайдено! Додай його з токеном бота.")

BOT_TOKEN = load_token()

# === WayForPay ===
# Обов'язково задай ці змінні у Railway → Variables
WFP_MERCHANT = os.getenv("WFP_MERCHANT", "")
WFP_SECRET = os.getenv("WFP_SECRET", "")
MERCHANT_DOMAIN = os.getenv("MERCHANT_DOMAIN", "example.com")

# Публічний URL твого сервісу Railway без слеша в кінці
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://your-app.up.railway.app")

# Сума підписки (грн)
SUBSCRIPTION_AMOUNT = int(os.getenv("SUBSCRIPTION_AMOUNT", "100"))

# Валюта
CURRENCY = "UAH"

# Файл з користувачами (проста JSON-пам'ять)
USERS_FILE = "users.json"
