
# VIP Fitness Bot — Рекурентна підписка (WayForPay)

## Кроки запуску на Railway
1. Завантаж цей ZIP у GitHub та задеплоюй із репозиторію.
2. У Railway → **Variables** додай:
   - `BOT_TOKEN` — токен Telegram бота
   - `WFP_MERCHANT` — merchantAccount з WayForPay
   - `WFP_SECRET` — SecretKey з WayForPay
   - `PUBLIC_URL` — домен Railway (`https://<app>.up.railway.app`)
   - `BOT_USERNAME` — юзернейм бота без @
   - (опц.) `WFP_RETURN_URL`
   - (опц.) `SUBSCRIPTION_AMOUNT` — сума, за замовчуванням 100
3. У WayForPay: вкажи **serviceUrl** = `https://<PUBLIC_URL>/wfp-callback`. Увімкни **Regular Payments** у кабінеті.
4. В Telegram: `/start` → натисни "Оплатити 100 грн". Після успішної оплати у callback прийде `recToken`. Бот збереже його.
5. Далі бот щоденно намагається автосписувати у дату `next_due_at`. Якщо 3 дні поспіль не виходить — рівень скидається до 0.

> Примітка: сигнатури для регулярних платежів та callback можуть відрізнятися залежно від налаштувань твого акаунта у WayForPay. Якщо WayForPay повертає помилку "Invalid merchantSignature" — відкоригуй порядок полів у функціях `sign_regular` або `sign_callback_check` згідно з документацією у твоєму кабінеті.
