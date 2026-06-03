# 🎰 Lucky Casino Bot

Telegram Casino Bot с мини-приложением и реальными выплатами через CryptoBot.

## 🎮 Игры
- 🎰 **Слоты** — до x50 за джекпот
- 🪙 **Монетка** — x1.95, 50/50
- 🎡 **Рулетка** — до x36 на число
- 🚀 **Краш** — сам выбери множитель кэшаута
- 🃏 **Блэкджек** — классика против дилера
- 🎲 **Кости** — до x5.5 за точное число

## 💰 Платежи
- Депозит через CryptoBot инвойс (USDT, TON, BTC, ETH, LTC)
- Вывод через transfer (прямой перевод) или check (чек)
- Авто-проверка оплаты

---

## 🚀 Быстрый старт

### 1. Получить токены

**Telegram Bot:**
1. Открой [@BotFather](https://t.me/BotFather) → `/newbot`
2. Скопируй токен

**CryptoBot:**
1. Открой [@CryptoBot](https://t.me/CryptoBot) (для тестнета: [@CryptoTestnetBot](https://t.me/CryptoTestnetBot))
2. Нажми **Start** → **My Apps** → **Create App**
3. Скопируй **API Token**

### 2. Установка

```bash
cd casino_bot
pip install -r requirements.txt
```

### 3. Настройка

```bash
cp .env.example .env
nano .env
```

Заполни `.env`:
```
BOT_TOKEN=твой_токен_бота
CRYPTO_PAY_TOKEN=твой_токен_cryptobot
WEBAPP_URL=https://твой-домен.com
ADMIN_IDS=твой_telegram_id
```

### 4. Хостинг WebApp

WebApp нужно хостить на HTTPS. Варианты:

**GitHub Pages (бесплатно):**
1. Создай репо на GitHub
2. Залей `webapp/index.html`
3. Settings → Pages → Enable
4. URL будет: `https://username.github.io/repo-name/`

**Vercel (бесплатно):**
```bash
cd webapp
npx vercel deploy
```

**VPS с nginx:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    root /var/www/casino-webapp;
    index index.html;
}
```

### 5. Настройка WebApp в BotFather

```
/mybots → твой бот → Bot Settings → Menu Button → Configure menu button
URL: https://твой-домен.com
Text: 🎰 Казино
```

### 6. Запуск бота

```bash
cd casino_bot
python bot/main.py
```

Или через systemd / pm2 для продакшена.

---

## ⚙️ Настройка CryptoBot для Transfer

Чтобы вывод работал через прямой перевод (transfer), нужно:
1. [@CryptoBot](https://t.me/CryptoBot) → My Apps → твоё приложение
2. **Transfer to users** → Enable
3. Если не включено — бот автоматически создаст чек вместо transfer

---

## 🛡️ Безопасность

- Никогда не публикуй `.env` в репозиторий
- Добавь `.env` в `.gitignore`
- Используй тестнет для разработки
- Проверяй баланс перед выводом
- Все операции логируются в БД

---

## 🗂️ Структура проекта

```
casino_bot/
├── bot/
│   └── main.py          # Точка входа
├── webapp/
│   └── index.html       # Мини-приложение
├── config.py            # Настройки
├── database.py          # SQLite БД
├── cryptopay.py         # CryptoBot API
├── games.py             # Логика игр
├── handlers.py          # Обработчики бота
├── keyboards.py         # Кнопки
├── requirements.txt
└── .env.example
```

---

## 📊 Хаус-эдж (преимущество казино)

| Игра | Хаус-эдж |
|------|-----------|
| Слоты | ~8% |
| Монетка | 5% |
| Рулетка (красное/чёрное) | ~2.7% |
| Рулетка (зелёное) | ~5% |
| Краш | 4% |
| Блэкджек | ~2% |
| Кости | ~8% |

---

## 🔧 Команды администратора

```
/admin            — баланс приложения
/addbalance <id> <amount>  — начислить баланс пользователю
```

---

## 📞 Поддержка

Если возникли вопросы по интеграции CryptoBot — читай официальную документацию:
https://help.crypt.bot/crypto-pay-api
