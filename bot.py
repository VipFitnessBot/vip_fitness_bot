import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta

import pytz
import requests
from flask import Flask, request, jsonify
from waitress import serve

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import (
    BOT_TOKEN, WFP_MERCHANT, WFP_SECRET, MERCHANT_DOMAIN, PUBLIC_URL,
    SUBSCRIPTION_AMOUNT, CURRENCY, USERS_FILE
)

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vip-bot")

KYIV_TZ = pytz.timezone("Europe/Kyiv")

# === ПРОСТЕ ЗБЕРЕЖЕННЯ КОРИСТУВАЧІВ ===
# Структура: {
#   str(user_id): {
#       "payments": int,
#       "level": int,
#       "last_paid_at": "iso",
#       "recToken": str|None
#   }
# }
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USERS = load_users()

# === КОНСТАНТИ РІВНІВ ===
# 1→20%, 2→25%, 3→30%, 4→35%, 5→40%, 6→45%
DISCOUNT_BY_PAYMENTS = {
    1: "20%",
    2: "25%",
    3: "30%",
    4: "35%",
    5: "40%",
    6: "45%",
}
# Бонуси:
BONUSES = {
    2: "Кава",
    3: "2 кави",
    4: "Протеїновий коктейль",
    5: "Кава + протеїновий коктейль",
    6: "2 кави + протеїновий коктейль",
}
ALL_DISCOUNTS_LIST = [
    "1 рівень → 20%",
    "2 рівень → 25%",
    "3 рівень → 30%",
    "4 рівень → 35%",
    "5 рівень → 40%",
    "6 рівень → 45%",
]
ALL_BONUSES_LIST = [
    "2 рівень → Кава",
    "3 рівень → 2 кави",
    "4 рівень → Протеїновий коктейль",
    "5 рівень → Кава + протеїновий коктейль",
    "6 рівень → 2 кави + протеїновий коктейль",
]

def payments_to_level(payments: int) -> int:
    return min(max(payments, 0), 6)

def touch_user(user_id: int):
    sid = str(user_id)
    if sid not in USERS:
        USERS[sid] = {"payments": 0, "level": 0, "last_paid_at": None, "recToken": None}
        save_users(USERS)

# === WayForPay: підпис для createInvoice ===
def wfp_signature(data_items):
    # об'єднання через ;
    base_str = ";".join(str(x) for x in data_items)
    digest = hmac.new(WFP_SECRET.encode("utf-8"), base_str.encode("utf-8"), hashlib.md5).hexdigest()
    return digest

def create_wfp_invoice(user_id: int) -> str:
    order_ref = f"vip_{user_id}_{int(time.time())}"
    order_date = int(time.time())
    amount = SUBSCRIPTION_AMOUNT

    # Мінімальні поля для createInvoice
    payload = {
        "transactionType": "CREATE_INVOICE",
        "merchantAccount": WFP_MERCHANT,
        "merchantDomainName": MERCHANT_DOMAIN,
        "orderReference": order_ref,
        "orderDate": order_date,
        "amount": amount,
        "currency": CURRENCY,
        "productName": ["VIP підписка"],
        "productPrice": [amount],
        "productCount": [1],
        "serviceUrl": f"{PUBLIC_URL}/wfp-callback",  # куди WayForPay шле результат
        "returnUrl": f"https://t.me/{BOT_USERNAME}"
    }

    # Підпис (див. документацію WayForPay: merchantSignature)
    # Послідовність: merchantAccount;merchantDomainName;orderReference;orderDate;amount;currency;productName[0];productCount[0];productPrice[0]
    sig_items = [
        payload["merchantAccount"],
        payload["merchantDomainName"],
        payload["orderReference"],
        payload["orderDate"],
        payload["amount"],
        payload["currency"],
        payload["productName"][0],
        payload["productCount"][0],
        payload["productPrice"][0],
    ]
    payload["merchantSignature"] = wfp_signature(sig_items)

    r = requests.post("https://api.wayforpay.com/api", json=payload, timeout=15)
    r.raise_for_status()
    resp = r.json()
    # Очікуємо invoiceUrl
    invoice_url = resp.get("invoiceUrl")
    if not invoice_url:
        raise RuntimeError(f"WayForPay error: {resp}")
    return invoice_url

# === Telegram Bot ===
BOT_USERNAME = ""  # підставимо з /start (для returnUrl)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_USERNAME
    if update.effective_chat.type == "private":
        BOT_USERNAME = context.bot.username

    user_id = update.effective_user.id
    touch_user(user_id)

    kb = [
        [InlineKeyboardButton("💳 Оплатити 100 грн (VIP)", callback_data="pay")],
        [InlineKeyboardButton("🎁 Мої бонуси", callback_data="bonuses"), InlineKeyboardButton("📉 Мої знижки", callback_data="discounts")],
        [InlineKeyboardButton("📊 Мій рівень", callback_data="level")],
        [InlineKeyboardButton("ℹ️ Усі можливості клубу", callback_data="all")]
    ]
    if update.message:
        await update.message.reply_text("Вітаю у VIP клубі! Обери опцію:", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.edit_message_text("Вітаю у VIP клубі! Обери опцію:", reply_markup=InlineKeyboardMarkup(kb))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    touch_user(user_id)
    sid = str(user_id)

    if query.data == "pay":
        # Створюємо реальний інвойс у WayForPay
        try:
            invoice_url = create_wfp_invoice(user_id)
            kb = [[InlineKeyboardButton("Перейти до оплати", url=invoice_url)]]
            await query.edit_message_text("🔗 Натисни кнопку, щоб оплатити 100 грн:", reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            log.exception("Помилка створення інвойсу")
            await query.edit_message_text(f"❌ Не вдалось створити оплату: {e}")

    elif query.data == "bonuses":
        level = USERS[sid]["level"]
        current = BONUSES.get(level, "Наразі бонусів немає. Піднімай рівень 😉")
        all_txt = "\n".join(ALL_BONUSES_LIST) + "\n\n*Бонуси можна обміняти на інші товари у схожому ціновому діапазоні."
        await query.edit_message_text(f"🎁 Твої бонуси: {current}\n\nДоступні бонуси за рівнями:\n{all_txt}")

    elif query.data == "discounts":
        level = USERS[sid]["level"]
        current = DISCOUNT_BY_PAYMENTS.get(level, "Ще немає знижки")
        all_txt = "\n".join(ALL_DISCOUNTS_LIST)
        await query.edit_message_text(f"📉 Твоя знижка: {current}\n\nДоступні знижки за рівнями:\n{all_txt}")

    elif query.data == "level":
        level = USERS[sid]["level"]
        p = USERS[sid]["payments"]
        last = USERS[sid]["last_paid_at"]
        last_txt = last if last else "—"
        await query.edit_message_text(f"📊 Твій рівень: {level} \nОплачених місяців: {p}\nОстання оплата: {last_txt}")

    elif query.data == "all":
        bonuses = "\n".join(ALL_BONUSES_LIST)
        discounts = "\n".join(ALL_DISCOUNTS_LIST)
        await query.edit_message_text(f"🎁 Бонуси:\n{bonuses}\n\n📉 Знижки:\n{discounts}\n\n*Бонуси можна обміняти на інші товари у схожому ціновому діапазоні.")

def inc_level_after_success(user_id: int):
    sid = str(user_id)
    touch_user(user_id)
    USERS[sid]["payments"] += 1
    USERS[sid]["level"] = payments_to_level(USERS[sid]["payments"])
    USERS[sid]["last_paid_at"] = datetime.now(KYIV_TZ).isoformat(timespec="seconds")
    save_users(USERS)

# === Flask для прийому callback від WayForPay ===
app = Flask(__name__)

@app.post("/wfp-callback")
def wfp_callback():
    try:
        data = request.get_json(force=True, silent=True) or {}
        log.info("WFP callback: %s", data)

        reason_code = str(data.get("reasonCode", ""))
        txn_status = data.get("transactionStatus", "")
        order_ref = data.get("orderReference", "")
        # Спробуємо витягти user_id з orderReference vip_{user_id}_{ts}
        uid = None
        if order_ref.startswith("vip_"):
            try:
                uid = int(order_ref.split("_")[1])
            except Exception:
                uid = None

        # Якщо успішно — оновлюємо рівень
        if txn_status in ("Approved", "InProcessing") and reason_code in ("1100", "0", ""):
            if uid:
                inc_level_after_success(uid)

        # Якщо прийде recToken (для рекурентів) — збережемо
        if uid and "recToken" in data:
            sid = str(uid)
            touch_user(uid)
            USERS[sid]["recToken"] = data.get("recToken")
            save_users(USERS)

        return jsonify({"code": "accept"})
    except Exception as e:
        log.exception("callback error")
        return jsonify({"code": "error", "message": str(e)}), 500

# === Фоновий задачник: щоденна перевірка прострочки (30+3 дні) ===
async def daily_overdue_check(app_telegram: Application):
    from datetime import datetime, timedelta
    while True:
        try:
            now = datetime.now(KYIV_TZ)
            for sid, u in list(USERS.items()):
                last = u.get("last_paid_at")
                if not last:
                    continue
                try:
                    last_dt = datetime.fromisoformat(last)
                except Exception:
                    continue
                # 33 дні від останньої оплати — скидання
                if now - last_dt > timedelta(days=33):
                    u["level"] = 0
                    u["payments"] = 0
            save_users(USERS)
        except Exception:
            pass
        await asyncio.sleep(24 * 60 * 60)

async def on_start(app_telegram: Application):
    asyncio.create_task(daily_overdue_check(app_telegram))

def run_flask():
    from waitress import serve
    import os
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))

async def main_async():
    application = Application.builder().token(BOT_TOKEN).post_init(on_start).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))

    # Flask у окремому потоці
    import threading
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    log.info("Bot is starting...")
    await application.run_polling()

if __name__ == "__main__":
    import os
    asyncio.run(main_async())
