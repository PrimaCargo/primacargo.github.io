import hashlib
import hmac
import json
import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = Path(os.getenv("DB_PATH", str(ROOT / "prima_cargo.db")))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
APP_ENV = os.getenv("APP_ENV", "production").lower()
app = FastAPI(title="PRIMA CARGO Mini App")

STATUS = {
    "ru": ["Ожидает приёма", "Принят в Китае", "Проверяется", "Собран", "Упакован", "Отправлен из Китая", "В пути", "Прибыл в Таджикистан", "Выдан клиенту"],
    "tg": ["Интизори қабул", "Дар Чин қабул шуд", "Санҷида мешавад", "Ҷамъ карда шуд", "Бастабандӣ шуд", "Аз Чин фиристода шуд", "Дар роҳ", "Ба Тоҷикистон расид", "Ба муштарӣ супурда шуд"],
    "en": ["Awaiting receipt", "Received in China", "Being checked", "Collected", "Packed", "Shipped from China", "In transit", "Arrived in Tajikistan", "Handed to customer"],
    "zh": ["等待收货", "已在中国收货", "检查中", "已集货", "已打包", "已从中国发出", "运输途中", "已抵达塔吉克斯坦", "已交付客户"],
}

@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")

def check_init_data(raw: str):
    if APP_ENV == "development":
        return "ru"
    if not TOKEN or not raw:
        raise HTTPException(401, "telegram_required")
    try:
        values = dict(parse_qsl(raw, keep_blank_values=True))
        their_hash = values.pop("hash")
        auth_date = int(values.get("auth_date", "0"))
        if time.time() - auth_date > 86400 or auth_date > time.time() + 60:
            raise ValueError("stale")
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, their_hash):
            raise ValueError("hash")
        user = json.loads(values["user"])
        return str(user.get("language_code", "ru"))
    except Exception:
        raise HTTPException(401, "telegram_required")

@app.get("/api/order")
def get_order(code: str, x_telegram_init_data: str = Header(default="")):
    lang_code = check_init_data(x_telegram_init_data)
    lang = "tg" if lang_code.startswith("tg") else "zh" if lang_code.startswith("zh") else "en" if lang_code.startswith("en") else "ru"
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT code,status,updated_at FROM orders WHERE code=?", (code.strip().upper(),)).fetchone()
    except sqlite3.Error:
        raise HTTPException(503, "database_unavailable")
    if not row:
        raise HTTPException(404, "not_found")
    status_num = int(row["status"])
    if not 0 <= status_num < 9:
        raise HTTPException(500, "invalid_status")
    return {"code": row["code"], "status": STATUS[lang][status_num], "updated_at": row["updated_at"].replace("T", " ")[:19] + " UTC"}




