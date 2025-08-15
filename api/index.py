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
    async wi
