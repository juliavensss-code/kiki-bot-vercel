import os
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

# Загружаем характер Кики
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
with open(os.path.join(BASE_DIR, "system_prompt.txt"), "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

async def chat_llm(user_id: int, text: str) -> str:
    # Если нет ключа OpenAI — мягкий фолбэк (ответ без ИИ)
    if not OPENAI_API_KEY:
        return ("Я рядом. Похоже, это важно. "
                "Хочешь, набросаю маленький план на 10 минут?")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"[user_id:{user_id}]\nСообщение: {text}"}
    ]
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={"model": MODEL, "messages": messages, "temperature": 0.7},
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

@app.get("/api/health")
async def health():
    return {"ok": True}

@app.get("/api/setup")
async def setup_webhook(request: Request, secret: str):
    # Одноразовая настройка вебхука
    if WEBHOOK_SECRET and secret != WEBHOOK_SECRET:
        raise HTTPException(403, "Bad secret")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    proto = request.headers.get("x-forwarded-proto", "https")
    token_prefix = BOT_TOKEN.split(":")[0]
    url = f"{proto}://{host}/api/webhook/{token_prefix}"

    params = {"url": url}
    if WEBHOOK_SECRET:
        params["secret_token"] = WEBHOOK_SECRET

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", params=params)
        ok = r.json()
    return {"setWebhook": ok, "webhook_url": url}

@app.post("/api/webhook/{token_prefix}")
async def telegram_webhook(
    token_prefix: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None)
):
    # Простейшие проверки
    if token_prefix != BOT_TOKEN.split(":")[0]:
        raise HTTPException(404, "Not found")
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(403, "Forbidden")

    data = await request.json()
    message = data.get("message") or data.get("edited_message") or {}
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return JSONResponse({"ok": True})

    if text:
        reply = await chat_llm(user_id=chat_id, text=text)
    else:
        reply = "Я пока понимаю только текст. Напиши словами — и я рядом."

    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )
    return JSONResponse({"ok": True})
