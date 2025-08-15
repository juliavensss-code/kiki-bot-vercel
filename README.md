# Kiki — Telegram bot (webhooks on Vercel)

Этот проект — FastAPI-приложение, работающее как Telegram webhook на Vercel (бесплатно).

## Переменные окружения на Vercel
- BOT_TOKEN — токен Telegram бота из @BotFather
- OPENAI_API_KEY — ключ OpenAI
- MODEL — gpt-4o-mini (по умолчанию)
- WEBHOOK_SECRET — любая случайная строка (защита webhook)

## Маршруты
- GET `/api/health` — проверка живости
- GET `/api/setup?secret=XXX` — установить webhook (XXX должен совпадать с WEBHOOK_SECRET)
- POST `/api/webhook/<token_prefix>` — получает апдейты Telegram

## Локально (необязательно)
- Установить зависимости: `pip install -r requirements.txt`
- Запустить: `uvicorn api.index:app --reload`
