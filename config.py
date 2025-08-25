import os

# Читаємо токен з token.txt
def load_token():
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError("Файл token.txt не знайдено! Створи його та встав токен.")

BOT_TOKEN = load_token()

# Дані WayForPay (поки що заглушки, заміниш своїми)
WFP_MERCHANT = os.getenv("WFP_MERCHANT", "demo")
WFP_SECRET = os.getenv("WFP_SECRET", "demo_secret")
WFP_URL = os.getenv("WFP_URL", "https://demo.wayforpay.com")
