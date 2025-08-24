
import os
import json
import time
import hmac
import hashlib
import threading
from datetime import datetime, timedelta

import requests
from flask import Flask, request, jsonify
import telebot
from telebot import types

# =====================
# Config / Secrets
# =====================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN and os.path.exists("token.txt"):
    with open("token.txt", "r", encoding="utf-8") as f:
        BOT_TOKEN = f.read().strip()
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не знайдено. Додай Railway Variable BOT_TOKEN або файл token.txt.")

# WayForPay
WFP_MERCHANT = os.environ.get("WFP_MERCHANT", "").strip()           # merchantAccount
WFP_SECRET   = os.environ.get("WFP_SECRET", "").strip()             # SecretKey
PUBLIC_URL   = os.environ.get("PUBLIC_URL", "").rstrip("/")         # https://<app>.up.railway.app
BOT_USERNAME = os.environ.get("BOT_USERNAME", "").strip()           # без @
WFP_RETURN_URL = os.environ.get("WFP_RETURN_URL", f"https://t.me/{BOT_USERNAME}")

# Витягнути домен для підпису (merchantDomainName)
if PUBLIC_URL.startswith("http"):
    from urllib.parse import urlparse
    WFP_DOMAIN = urlparse(PUBLIC_URL).netloc
else:
    WFP_DOMAIN = os.environ.get("WFP_DOMAIN", "your-domain.example")

# Сума підписки
SUBSCRIPTION_AMOUNT = int(os.environ.get("SUBSCRIPTION_AMOUNT", "100"))  # грн

# =====================
# Data Storage
# =====================

DATA_FILE = "users.json"

def load_db():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_db():
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

DB = load_db()

def get_user(uid: int):
    uid = str(uid)
    if uid not in DB:
        DB[uid] = {
            "level": 0,
            "consecutive_payments": 0,
            "last_payment_at": None,
            "next_due_at": None,
            "failed_autopay_days": 0,
            "recToken": None,
            "payments": []  # [{orderRef, amount, status, createdAt}]
        }
        save_db()
    return DB[uid]

# =====================
# VIP Logic
# =====================

def level_from_consecutive(n: int) -> int:
    if n <= 0: return 0
    lvl = (n - 1)//2 + 1
    return min(lvl, 6)  # до 45%

def discount_for_level(level: int) -> int:
    return {0:0, 1:20, 2:25, 3:30, 4:35, 5:40, 6:45}.get(level, 45)

BONUSES_BY_LEVEL = {
    0: "— Бонуси з’являться з рівня 2.",
    1: "— Поки бонусів немає.",
    2: "— 1× кава",
    3: "— 2× кави",
    4: "— 1× протеїновий коктейль",
    5: "— кава + протеїновий коктейль",
    6: "— 2× кави + 1× протеїновий коктейль\n(можна обміняти на інші товари у схожому діапазоні)"
}

def discounts_text():
    return "\n".join([
        "💸 Знижки на абонементи:",
        "1–2 оплати → 20%",
        "3–4 оплати → 25%",
        "5–6 оплат → 30%",
        "7–8 оплат → 35%",
        "9–10 оплат → 40%",
        "11+ оплат → 45%",
    ])

def bonuses_text():
    return "\n".join([
        "🎁 Бонуси за рівнями:",
        "2 рівень: 1× кава",
        "3 рівень: 2× кави",
        "4 рівень: 1× протеїновий коктейль",
        "5 рівень: кава + протеїновий коктейль",
        "6 рівень: 2× кави + 1× протеїновий коктейль",
        "🔁 Можна обміняти на інші товари у схожому діапазоні."
    ])

# =====================
# WayForPay helpers
# =====================

def hmac_md5(secret: str, parts: list) -> str:
    base = ";".join(str(p) for p in parts)
    return hmac.new(secret.encode("utf-8"), base.encode("utf-8"), hashlib.md5).hexdigest()

def sign_purchase(order_ref, order_date, amount, currency, product_names, product_counts, product_prices):
    parts = [WFP_MERCHANT, WFP_DOMAIN, order_ref, order_date, amount, currency]
    parts += list(product_names)
    parts += [str(x) for x in product_counts]
    parts += [str(x) for x in product_prices]
    return hmac_md5(WFP_SECRET, parts)

def create_payment_link(user_id: int, amount_uah: int):
    """Перша оплата (ручна). Дає URL і, після success, у callback прийде recToken."""
    if not (WFP_MERCHANT and WFP_SECRET and PUBLIC_URL):
        return {"ok": False, "error": "WayForPay не налаштовано. Додай WFP_MERCHANT, WFP_SECRET, PUBLIC_URL."}

    order_ref = f"vip_{user_id}_{int(time.time())}"
    order_date = int(time.time())
    currency = "UAH"
    product_names = ["VIP клуб — щомісячний внесок"]
    product_counts = [1]
    product_prices = [amount_uah]

    signature = sign_purchase(order_ref, order_date, amount_uah, currency, product_names, product_counts, product_prices)

    form = {
        "merchantAccount": WFP_MERCHANT,
        "merchantAuthType": "SimpleSignature",
        "merchantDomainName": WFP_DOMAIN,
        "merchantSignature": signature,
        "orderReference": order_ref,
        "orderDate": order_date,
        "amount": amount_uah,
        "currency": currency,
        "productName[]": product_names,
        "productCount[]": product_counts,
        "productPrice[]": product_prices,
        "returnUrl": WFP_RETURN_URL,
        "serviceUrl": f"{PUBLIC_URL}/wfp-callback",
        "language": "uk",
        "regularMode": "true"  # важливо: дозволяє зберегти recToken після success
    }

    try:
        r = requests.post("https://secure.wayforpay.com/pay?behavior=offline", data=form, timeout=20)
        r.raise_for_status()
        data = r.json()
        if "url" in data:
            return {"ok": True, "url": data["url"], "orderRef": order_ref}
        return {"ok": False, "error": f"Відповідь WayForPay без url: {data}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def sign_regular(order_ref, amount, currency, rec_token):
    """Підпис для регулярного списання. У більшості інтеграцій WayForPay він включає
    merchantAccount;orderReference;amount;currency;recToken (HMAC-MD5).
    За потреби звір у кабінеті WFP і поправ parts.
    """
    parts = [WFP_MERCHANT, order_ref, amount, currency, rec_token]
    return hmac_md5(WFP_SECRET, parts)

def regular_charge(user_id: int, amount_uah: int) -> dict:
    """Спроба автосписання по recToken. Повертає dict ok/err. """
    uid = str(user_id)
    u = get_user(user_id)
    rec = u.get("recToken")
    if not rec:
        return {"ok": False, "error": "recToken відсутній (перша оплата ще не дала токен)."}

    order_ref = f"vip_auto_{uid}_{int(time.time())}"
    currency = "UAH"
    sign = sign_regular(order_ref, amount_uah, currency, rec)

    payload = {
        "transactionType": "REGULAR_PAYMENT",
        "merchantAccount": WFP_MERCHANT,
        "merchantAuthType": "SimpleSignature",
        "merchantSignature": sign,
        "orderReference": order_ref,
        "amount": amount_uah,
        "currency": currency,
        "recToken": rec,
        "productName": ["VIP клуб — автосписання"],
        "productPrice": [amount_uah],
        "productCount": [1]
    }

    try:
        r = requests.post("https://api.wayforpay.com/api", json=payload, timeout=25)
        r.raise_for_status()
        data = r.json()
        status = data.get("transactionStatus", "")
        if status == "Approved":
            return {"ok": True, "data": data, "orderRef": order_ref}
        return {"ok": False, "error": f"WFP status: {status} / {data}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# =====================
# Telegram Bot UI
# =====================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(f"💳 Оплатити {SUBSCRIPTION_AMOUNT} грн (перший платіж)"))
    kb.add(types.KeyboardButton("📊 Мій рівень"), types.KeyboardButton("💸 Знижки"))
    kb.add(types.KeyboardButton("🎁 Бонуси"))
    return kb

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message):
    get_user(m.from_user.id)
    bot.send_message(
        m.chat.id,
        f"Вітаємо у VIP клубі 🎟️\nЩомісячний внесок: <b>{SUBSCRIPTION_AMOUNT} грн</b>.\n"
        "Перший платіж — вручну, далі буде автосписання по картці (за згодою клієнта).",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == "💸 Знижки")
def show_discounts(m):
    bot.send_message(m.chat.id, discounts_text())

@bot.message_handler(func=lambda msg: msg.text == "🎁 Бонуси")
def show_bonuses(m):
    bot.send_message(m.chat.id, bonuses_text())

@bot.message_handler(func=lambda msg: msg.text == "📊 Мій рівень")
def my_level(m):
    u = get_user(m.from_user.id)
    level = u["level"]
    disc = discount_for_level(level)
    last = u["last_payment_at"]
    last_str = datetime.fromtimestamp(last).strftime("%d.%m.%Y %H:%M") if last else "—"
    rec = "✅ збережено" if u.get("recToken") else "❌ ще немає (з’явиться після 1-го успішного платежу)"
    text = (
        f"👤 Рівень: <b>{level}</b> (знижка {disc}%)\n"
        f"Остання оплата: {last_str}\n"
        f"recToken: {rec}\n"
        f"Бонуси:\n{BONUSES_BY_LEVEL.get(level, '')}"
    )
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text.startswith("💳 Оплатити"))
def pay_first(m):
    uid = m.from_user.id
    res = create_payment_link(uid, SUBSCRIPTION_AMOUNT)
    if not res["ok"]:
        bot.send_message(m.chat.id, f"Помилка створення платежу: {res['error']}")
        return

    # Запишемо "Pending"
    u = get_user(uid)
    u["payments"].append({
        "orderRef": res["orderRef"],
        "amount": SUBSCRIPTION_AMOUNT,
        "status": "Pending",
        "createdAt": int(time.time())
    })
    save_db()

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"Оплатити {SUBSCRIPTION_AMOUNT} грн", url=res["url"]))
    bot.send_message(m.chat.id, "Натисни, щоб оплатити:", reply_markup=kb)

# =====================
# Flask: serviceUrl callback від WayForPay
# =====================

server = Flask(__name__)

def sign_callback_check(payload: dict) -> bool:
    # В signature для callback зазвичай входить:
    # merchantAccount;orderReference;amount;currency;authCode;cardPan;transactionStatus;reasonCode
    try:
        parts = [
            payload.get("merchantAccount",""),
            payload.get("orderReference",""),
            payload.get("amount",""),
            payload.get("currency",""),
            payload.get("authCode",""),
            payload.get("cardPan",""),
            payload.get("transactionStatus",""),
            payload.get("reasonCode",""),
        ]
        expected = hmac_md5(WFP_SECRET, parts)
        return expected == payload.get("merchantSignature")
    except Exception:
        return False

def callback_response(order_ref: str, status: str = "accept"):
    now = int(time.time())
    sig = hmac_md5(WFP_SECRET, [order_ref, status, now])
    return {"orderReference": order_ref, "status": status, "time": now, "signature": sig}

@server.route("/wfp-callback", methods=["POST"])
def wfp_callback():
    # Приймаємо JSON або form-encoded
    payload = request.get_json(silent=True)
    if not payload:
        payload = request.form.to_dict()
    order_ref = payload.get("orderReference", "unknown")
    tx_status = payload.get("transactionStatus", "")
    # Витягуємо tg_id з orderRef vip_<tg>_<ts>
    tg_id = None
    if order_ref.startswith("vip_"):
        try:
            tg_id = int(order_ref.split("_")[1])
        except Exception:
            pass

    # Перевірка підпису (якщо помилка — все одно відповідаємо accept, але не зараховуємо)
    valid = sign_callback_check(payload)

    if valid and tx_status == "Approved" and tg_id:
        u = get_user(tg_id)
        # Зберегти recToken, якщо надійшов від WayForPay після успішного платежу
        rec_token = payload.get("recToken") or payload.get("recTokenForInstallments")
        if rec_token:
            u["recToken"] = rec_token

        # Оновити оплати
        already = any(p["orderRef"] == order_ref and p.get("status") == "Approved" for p in u["payments"])
        if not already:
            # Маркуємо як Approved
            for p in u["payments"]:
                if p["orderRef"] == order_ref:
                    p["status"] = "Approved"
                    break
            else:
                u["payments"].append({"orderRef": order_ref, "amount": payload.get("amount", SUBSCRIPTION_AMOUNT), "status": "Approved", "createdAt": int(time.time())})

            u["consecutive_payments"] = int(u.get("consecutive_payments", 0)) + 1
            u["level"] = level_from_consecutive(u["consecutive_payments"])
            u["last_payment_at"] = int(time.time())
            # Наступна дата списання через 30 днів
            u["next_due_at"] = u["last_payment_at"] + 30*24*3600
            u["failed_autopay_days"] = 0
            save_db()

            try:
                disc = discount_for_level(u["level"])
                bot.send_message(tg_id, f"✅ Оплату отримано! Рівень: {u['level']} (знижка {disc}%). Наступне списання автоматично через 30 днів.")
            except Exception:
                pass

    # Відповідь WayForPay
    return jsonify(callback_response(order_ref, "accept"))

# =====================
# Автосписання (щоденна перевірка)
# =====================

def daily_billing_loop():
    while True:
        now = int(time.time())
        changed = False
        for uid, u in list(DB.items()):
            # Якщо призначено дата наступного списання і recToken є
            due = u.get("next_due_at")
            rec = u.get("recToken")
            if not due or not rec:
                continue
            # Якщо настав час списання (перевіряємо раз на добу/годину)
            if now >= due:
                # Спробувати списати
                res = regular_charge(int(uid), SUBSCRIPTION_AMOUNT)
                if res.get("ok"):
                    # Успіх: оновлюємо стейт
                    u["payments"].append({
                        "orderRef": res.get("orderRef"),
                        "amount": SUBSCRIPTION_AMOUNT,
                        "status": "Approved",
                        "createdAt": int(time.time())
                    })
                    u["consecutive_payments"] = int(u.get("consecutive_payments", 0)) + 1
                    u["level"] = level_from_consecutive(u["consecutive_payments"])
                    u["last_payment_at"] = int(time.time())
                    u["next_due_at"] = u["last_payment_at"] + 30*24*3600
                    u["failed_autopay_days"] = 0
                    try:
                        disc = discount_for_level(u["level"])
                        bot.send_message(int(uid), f"✅ Автосписання {SUBSCRIPTION_AMOUNT} грн успішне. Рівень: {u['level']} (знижка {disc}%).")
                    except Exception:
                        pass
                    changed = True
                else:
                    # Не вдалося списати сьогодні
                    u["failed_autopay_days"] = int(u.get("failed_autopay_days", 0)) + 1
                    try:
                        bot.send_message(int(uid), "⚠️ Не вдалось автосписання сьогодні. Ми спробуємо знову завтра (3 спроби максимум).")
                    except Exception:
                        pass
                    # Якщо 3 дні поспіль не вдалося — рівень скидаємо
                    if u["failed_autopay_days"] >= 3:
                        u["level"] = 0
                        u["consecutive_payments"] = 0
                        u["next_due_at"] = None
                        try:
                            bot.send_message(int(uid), "⛔ Підписку прострочено >3 днів. Рівень VIP скинуто до 0. Оформіть повторно перший платіж, щоб відновити автосписання.")
                        except Exception:
                            pass
                        changed = True
            # end if due
        # end for users

        if changed:
            save_db()

        # Спимо годину (можна збільшити до 6 годин)
        time.sleep(3600)

# =====================
# Run (Railway expects a web server)
# =====================

def run_bot():
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)

if __name__ == "__main__":
    threading.Thread(target=daily_billing_loop, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", "8080"))
    server.run(host="0.0.0.0", port=port)
