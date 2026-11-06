import asyncio
import os
import sqlite3
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
DB_PATH = os.getenv("DB_PATH", "prima_cargo.db")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add it to the .env file in the project folder.")

TEXT = {
    "ru": {
        "choose": "Добро пожаловать в PRIMA CARGO!\nВыберите язык:",
        "language_saved": "Язык сохранён: Русский.",
        "menu": "Главное меню PRIMA CARGO. Выберите действие:",
        "track": "Введите код вашего заказа (например, PC-10245):",
        "not_found": "Заказ с таким кодом не найден. Проверьте код и попробуйте ещё раз.",
        "order": "📦 Заказ: {code}\nСтатус: {status}\nПоследнее обновление: {updated}",
        "language": "Выберите язык:",
        "support": "Если нужна помощь, свяжитесь с поддержкой PRIMA CARGO.",
        "cancel": "Отмена",
        "employee": "Панель сотрудника. Введите код заказа, чтобы найти его:",
        "updated": "Статус заказа {code} обновлён: {status}.",
        "choose_status": "Выберите новый статус для заказа {code}:",
        "no_access": "У вас нет доступа к этой панели.",
        "admin_help": "Команды администратора:\n/add_employee TELEGRAM_ID — добавить сотрудника\n/remove_employee TELEGRAM_ID — удалить сотрудника\n/add_order CODE — создать заказ\n/orders — последние заказы\n\nУзнать Telegram ID можно через @userinfobot.",
        "created": "Заказ {code} создан. Начальный статус: Ожидает приёма.",
        "exists": "Такой код уже существует.",
        "employee_added": "Сотрудник {uid} добавлен.",
        "employee_removed": "Сотрудник {uid} удалён.",
        "bad_id": "Укажите числовой Telegram ID. Пример: /add_employee 123456789",
        "new_order": "Введите код заказа, например PC-10245.",
        "orders": "Последние заказы:\n{items}",
        "empty": "Пока заказов нет.",
        "status_0": "Ожидает приёма",
        "status_1": "Принят в Китае",
        "status_2": "Проверяется",
        "status_3": "Собран",
        "status_4": "Упакован",
        "status_5": "Отправлен из Китая",
        "status_6": "В пути",
        "status_7": "Прибыл в Таджикистан",
        "status_8": "Выдан клиенту",
        "staff_menu": "🧰 Панель сотрудника",
        "admin_menu": "⚙️ Панель администратора",
        "client_menu": "📦 Отследить заказ",
        "language_button": "🌐 Язык",
        "back_menu": "↩️ Назад в меню",
        "china_address_button": "📍 Адрес в Китае",
        "china_address_unavailable": "📍 Адрес в Китае пока не указан. Мы добавим его позже.",
        "admin_add_order": "➕ Создать заказ",
        "admin_add_employee": "👤 Добавить сотрудника",
        "admin_remove_employee": "🚫 Удалить сотрудника",
        "admin_orders": "📋 Список заказов",
        "enter_employee_id": "Введите числовой Telegram ID сотрудника:",
    },
    "tg": {
        "choose": "Ба PRIMA CARGO хуш омадед!\nЗабонро интихоб кунед:",
        "language_saved": "Забон интихоб шуд: Тоҷикӣ.",
        "menu": "Менюи асосии PRIMA CARGO. Амалро интихоб кунед:",
        "track": "Рамзи фармоиши худро ворид кунед (масалан, PC-10245):",
        "not_found": "Фармоиш бо ин рамз ёфт нашуд. Рамзро санҷед.",
        "order": "📦 Фармоиш: {code}\nҲолат: {status}\nНавсозии охирин: {updated}",
        "language": "Забонро интихоб кунед:",
        "support": "Барои кӯмак ба дастгирии PRIMA CARGO муроҷиат кунед.",
        "cancel": "Бекор кардан",
        "employee": "Панели корманд. Барои ёфтани фармоиш рамзро ворид кунед:",
        "updated": "Ҳолати фармоиши {code} нав шуд: {status}.",
        "choose_status": "Ҳолати нави фармоиши {code}-ро интихоб кунед:",
        "no_access": "Шумо ба ин панел дастрасӣ надоред.",
        "admin_help": "Фармонҳои маъмур:\n/add_employee TELEGRAM_ID — илова кардани корманд\n/remove_employee TELEGRAM_ID — хориҷ кардани корманд\n/add_order CODE — сохтани фармоиш\n/orders — фармоишҳои охирин\n\nTelegram ID-ро аз @userinfobot гирифтан мумкин аст.",
        "created": "Фармоиши {code} сохта шуд. Ҳолати аввал: Интизори қабул.",
        "exists": "Ин рамз аллакай вуҷуд дорад.",
        "employee_added": "Корманди {uid} илова шуд.",
        "employee_removed": "Корманди {uid} хориҷ шуд.",
        "bad_id": "Telegram ID-и рақамиро ворид кунед. Мисол: /add_employee 123456789",
        "new_order": "Рамзи фармоишро ворид кунед, масалан PC-10245.",
        "orders": "Фармоишҳои охирин:\n{items}",
        "empty": "Ҳоло фармоиш нест.",
        "status_0": "Интизори қабул",
        "status_1": "Дар Чин қабул шуд",
        "status_2": "Санҷида мешавад",
        "status_3": "Ҷамъ карда шуд",
        "status_4": "Бастабандӣ шуд",
        "status_5": "Аз Чин фиристода шуд",
        "status_6": "Дар роҳ",
        "status_7": "Ба Тоҷикистон расид",
        "status_8": "Ба муштарӣ супурда шуд",
        "staff_menu": "🧰 Панели корманд",
        "admin_menu": "⚙️ Панели маъмур",
        "client_menu": "📦 Пайгирии фармоиш",
        "language_button": "🌐 Забон",
        "back_menu": "↩️ Бозгашт ба меню",
        "china_address_button": "📍 Суроға дар Чин",
        "china_address_unavailable": "📍 Суроға дар Чин ҳоло нишон дода нашудааст. Баъдтар илова мекунем.",
        "admin_add_order": "➕ Сохтани фармоиш",
        "admin_add_employee": "👤 Илова кардани корманд",
        "admin_remove_employee": "🚫 Хориҷ кардани корманд",
        "admin_orders": "📋 Рӯйхати фармоишҳо",
        "enter_employee_id": "Telegram ID-и рақамии кормандро ворид кунед:",
    },
    "en": {
        "choose": "Welcome to PRIMA CARGO!\nPlease choose your language:",
        "language_saved": "Language saved: English.",
        "menu": "PRIMA CARGO main menu. Choose an action:",
        "track": "Enter your order code (for example, PC-10245):",
        "not_found": "No order found with that code. Please check it and try again.",
        "order": "📦 Order: {code}\nStatus: {status}\nLast updated: {updated}",
        "language": "Choose your language:",
        "support": "Please contact PRIMA CARGO support if you need help.",
        "cancel": "Cancel",
        "employee": "Staff panel. Enter an order code to find it:",
        "updated": "Order {code} status updated: {status}.",
        "choose_status": "Choose a new status for order {code}:",
        "no_access": "You do not have access to this panel.",
        "admin_help": "Admin commands:\n/add_employee TELEGRAM_ID — add staff member\n/remove_employee TELEGRAM_ID — remove staff member\n/add_order CODE — create an order\n/orders — show recent orders\n\nGet a Telegram ID from @userinfobot.",
        "created": "Order {code} created. Initial status: Awaiting receipt.",
        "exists": "This code already exists.",
        "employee_added": "Staff member {uid} added.",
        "employee_removed": "Staff member {uid} removed.",
        "bad_id": "Enter a numeric Telegram ID. Example: /add_employee 123456789",
        "new_order": "Enter an order code, for example PC-10245.",
        "orders": "Recent orders:\n{items}",
        "empty": "There are no orders yet.",
        "status_0": "Awaiting receipt",
        "status_1": "Received in China",
        "status_2": "Being checked",
        "status_3": "Collected",
        "status_4": "Packed",
        "status_5": "Shipped from China",
        "status_6": "In transit",
        "status_7": "Arrived in Tajikistan",
        "status_8": "Handed to customer",
        "staff_menu": "🧰 Staff panel",
        "admin_menu": "⚙️ Admin panel",
        "client_menu": "📦 Track an order",
        "language_button": "🌐 Language",
        "back_menu": "↩️ Back to menu",
        "china_address_button": "📍 China address",
        "china_address_unavailable": "📍 The China address is not available yet. We will add it later.",
        "admin_add_order": "➕ Create order",
        "admin_add_employee": "👤 Add staff member",
        "admin_remove_employee": "🚫 Remove staff member",
        "admin_orders": "📋 Orders list",
        "enter_employee_id": "Enter the staff member's numeric Telegram ID:",
    },
    "zh": {
        "choose": "欢迎使用 PRIMA CARGO！\n请选择语言：",
        "language_saved": "语言已设置：中文。",
        "menu": "PRIMA CARGO 主菜单，请选择操作：",
        "track": "请输入订单编号（例如 PC-10245）：",
        "not_found": "未找到此订单，请检查编号后重试。",
        "order": "📦 订单：{code}\n状态：{status}\n最近更新：{updated}",
        "language": "请选择语言：",
        "support": "如需帮助，请联系 PRIMA CARGO 客服。",
        "cancel": "取消",
        "employee": "员工面板。请输入订单编号进行查询：",
        "updated": "订单 {code} 状态已更新：{status}。",
        "choose_status": "请选择订单 {code} 的新状态：",
        "no_access": "您无权使用此面板。",
        "admin_help": "管理员命令：\n/add_employee TELEGRAM_ID — 添加员工\n/remove_employee TELEGRAM_ID — 删除员工\n/add_order CODE — 创建订单\n/orders — 查看最近订单\n\n可通过 @userinfobot 查询 Telegram ID。",
        "created": "订单 {code} 已创建。初始状态：等待收货。",
        "exists": "此订单编号已存在。",
        "employee_added": "员工 {uid} 已添加。",
        "employee_removed": "员工 {uid} 已删除。",
        "bad_id": "请输入数字 Telegram ID，例如：/add_employee 123456789",
        "new_order": "请输入订单编号，例如 PC-10245。",
        "orders": "最近订单：\n{items}",
        "empty": "目前没有订单。",
        "status_0": "等待收货",
        "status_1": "已在中国收货",
        "status_2": "检查中",
        "status_3": "已集货",
        "status_4": "已打包",
        "status_5": "已从中国发出",
        "status_6": "运输途中",
        "status_7": "已抵达塔吉克斯坦",
        "status_8": "已交付客户",
        "staff_menu": "🧰 员工面板",
        "admin_menu": "⚙️ 管理员面板",
        "client_menu": "📦 查询订单",
        "language_button": "🌐 语言",
        "back_menu": "↩️ 返回主菜单",
        "china_address_button": "📍 中国地址",
        "china_address_unavailable": "📍 中国地址暂未公布，之后会在这里更新。",
        "admin_add_order": "➕ 创建订单",
        "admin_add_employee": "👤 添加员工",
        "admin_remove_employee": "🚫 删除员工",
        "admin_orders": "📋 订单列表",
        "enter_employee_id": "请输入员工的数字 Telegram ID：",
    },
}
STATUS_COUNT = 9
user_lang = {}
pending_action = {}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            code TEXT PRIMARY KEY,
            status INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            updated_by INTEGER
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS employees (
            user_id INTEGER PRIMARY KEY,
            added_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL DEFAULT 'ru'
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS order_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            status INTEGER NOT NULL,
            changed_at TEXT NOT NULL,
            changed_by INTEGER
        )""")

def get_lang(uid):
    if uid in user_lang:
        return user_lang[uid]
    with db() as con:
        row = con.execute("SELECT language FROM users WHERE user_id=?", (uid,)).fetchone()
    return row["language"] if row else "ru"

def set_lang(uid, lang):
    user_lang[uid] = lang
    with db() as con:
        con.execute("INSERT INTO users(user_id,language) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET language=excluded.language", (uid, lang))

def tr(uid, key, **kwargs):
    lang = get_lang(uid)
    return TEXT[lang].get(key, TEXT["ru"].get(key, key)).format(**kwargs)

def is_admin(uid):
    return uid in ADMIN_IDS

def is_employee(uid):
    if is_admin(uid):
        return True
    with db() as con:
        return con.execute("SELECT 1 FROM employees WHERE user_id=?", (uid,)).fetchone() is not None

def status_name(lang, status):
    return TEXT[lang][f"status_{status}"]

def main_keyboard(uid):
    rows = [
        [KeyboardButton(text=tr(uid, "client_menu"))],
        [KeyboardButton(text=tr(uid, "china_address_button"))],
        [KeyboardButton(text=tr(uid, "language_button"))],
    ]
    if is_employee(uid):
        rows.append([KeyboardButton(text=tr(uid, "staff_menu"))])
    if is_admin(uid):
        rows.append([KeyboardButton(text=tr(uid, "admin_menu"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def admin_keyboard(uid):
    rows = [
        [KeyboardButton(text=tr(uid, "admin_add_order"))],
        [KeyboardButton(text=tr(uid, "admin_add_employee")), KeyboardButton(text=tr(uid, "admin_remove_employee"))],
        [KeyboardButton(text=tr(uid, "admin_orders"))],
        [KeyboardButton(text=tr(uid, "back_menu"))],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

LANGUAGE_BUTTONS = {
    "🇷🇺 Русский": "ru",
    "🇹🇯 Тоҷикӣ": "tg",
    "🇬🇧 English": "en",
    "🇨🇳 中文": "zh",
}

STATUS_ICONS = ("⏳", "🇨🇳", "🔍", "📦", "🧳", "🚢", "🚚", "🇹🇯", "✅")

def language_keyboard(uid):
    rows = [[KeyboardButton(text=label)] for label in LANGUAGE_BUTTONS]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)

def order_status_keyboard(code, lang):
    rows = [[KeyboardButton(text=f"{STATUS_ICONS[i]} {status_name(lang, i)}")] for i in range(STATUS_COUNT)]
    rows.append([KeyboardButton(text=TEXT[lang]["back_menu"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)

async def notify_order_owner(bot, code, status):
    # The customer who last submitted this code is not assumed to be its owner.
    # Notifications can be enabled safely after adding an explicit order-owner field.
    return

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    uid = message.from_user.id
    with db() as con:
        row = con.execute("SELECT language FROM users WHERE user_id=?", (uid,)).fetchone()
    if not row:
        await message.answer(TEXT["ru"]["choose"], reply_markup=language_keyboard(uid))
    else:
        await message.answer(tr(uid, "menu"), reply_markup=main_keyboard(uid))

@dp.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    if lang not in TEXT:
        await callback.answer()
        return
    set_lang(callback.from_user.id, lang)
    await callback.message.edit_text(tr(callback.from_user.id, "language_saved"))
    await callback.message.answer(tr(callback.from_user.id, "menu"), reply_markup=main_keyboard(callback.from_user.id))
    await callback.answer()

@dp.message(Command("language"))
async def language_command(message: Message):
    await message.answer(tr(message.from_user.id, "language"), reply_markup=language_keyboard(message.from_user.id))

@dp.message(Command("admin"))
async def admin_help(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(tr(message.from_user.id, "no_access"))
        return
    await message.answer(tr(message.from_user.id, "admin_help"))

@dp.message(Command("add_employee"))
async def add_employee(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(tr(message.from_user.id, "no_access"))
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(tr(message.from_user.id, "bad_id"))
        return
    uid = int(parts[1])
    with db() as con:
        con.execute("INSERT OR IGNORE INTO employees(user_id,added_at) VALUES(?,?)", (uid, datetime.now(timezone.utc).isoformat()))
    await message.answer(tr(message.from_user.id, "employee_added", uid=uid))

@dp.message(Command("remove_employee"))
async def remove_employee(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(tr(message.from_user.id, "no_access"))
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(tr(message.from_user.id, "bad_id"))
        return
    uid = int(parts[1])
    with db() as con:
        con.execute("DELETE FROM employees WHERE user_id=?", (uid,))
    await message.answer(tr(message.from_user.id, "employee_removed", uid=uid))

@dp.message(Command("add_order"))
async def add_order(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(tr(message.from_user.id, "no_access"))
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        await message.answer(tr(message.from_user.id, "new_order"))
        return
    code = parts[1].strip().upper()
    now = datetime.now(timezone.utc).isoformat()
    try:
        with db() as con:
            con.execute("INSERT INTO orders(code,status,updated_at,updated_by) VALUES(?,0,?,?)", (code, now, message.from_user.id))
            con.execute("INSERT INTO order_history(code,status,changed_at,changed_by) VALUES(?,0,?,?)", (code, now, message.from_user.id))
        await message.answer(tr(message.from_user.id, "created", code=code))
    except sqlite3.IntegrityError:
        await message.answer(tr(message.from_user.id, "exists"))

@dp.message(Command("orders"))
async def list_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(tr(message.from_user.id, "no_access"))
        return
    with db() as con:
        rows = con.execute("SELECT code,status FROM orders ORDER BY updated_at DESC LIMIT 20").fetchall()
    if not rows:
        await message.answer(tr(message.from_user.id, "empty"))
        return
    lang = get_lang(message.from_user.id)
    items = "\n".join(f"• {r['code']} — {status_name(lang, r['status'])}" for r in rows)
    await message.answer(tr(message.from_user.id, "orders", items=items))

@dp.message(F.text)
async def text_router(message: Message):
    uid = message.from_user.id
    text = message.text.strip()
    if text in LANGUAGE_BUTTONS:
        lang = LANGUAGE_BUTTONS[text]
        set_lang(uid, lang)
        pending_action.pop(uid, None)
        await message.answer(tr(uid, "language_saved"), reply_markup=main_keyboard(uid))
        await message.answer(tr(uid, "menu"), reply_markup=main_keyboard(uid))
        return
    if text == tr(uid, "language_button"):
        await message.answer(tr(uid, "language"), reply_markup=language_keyboard(uid))
        return
    if text == tr(uid, "china_address_button"):
        await message.answer(tr(uid, "china_address_unavailable"), reply_markup=main_keyboard(uid))
        return
    if text == tr(uid, "back_menu"):
        pending_action.pop(uid, None)
        await message.answer(tr(uid, "menu"), reply_markup=main_keyboard(uid))
        return
    if text == tr(uid, "client_menu"):
        pending_action[uid] = "track"
        await message.answer(tr(uid, "track"))
        return
    if text == tr(uid, "staff_menu"):
        if not is_employee(uid):
            await message.answer(tr(uid, "no_access"))
            return
        pending_action[uid] = "staff_search"
        await message.answer(tr(uid, "employee"))
        return
    if text == tr(uid, "admin_menu"):
        if not is_admin(uid):
            await message.answer(tr(uid, "no_access"))
            return
        await message.answer(tr(uid, "admin_help"), reply_markup=admin_keyboard(uid))
        return
    admin_actions = {
        tr(uid, "admin_add_order"): "admin_add_order",
        tr(uid, "admin_add_employee"): "admin_add_employee",
        tr(uid, "admin_remove_employee"): "admin_remove_employee",
    }
    if is_admin(uid) and text == tr(uid, "admin_orders"):
        with db() as con:
            rows = con.execute("SELECT code,status FROM orders ORDER BY updated_at DESC LIMIT 20").fetchall()
        if not rows:
            await message.answer(tr(uid, "empty"), reply_markup=admin_keyboard(uid))
        else:
            items = "\n".join(f"• {r['code']} — {status_name(get_lang(uid), r['status'])}" for r in rows)
            await message.answer(tr(uid, "orders", items=items), reply_markup=admin_keyboard(uid))
        return
    if is_admin(uid) and text in admin_actions:
        pending_action[uid] = admin_actions[text]
        prompt = tr(uid, "new_order") if admin_actions[text] == "admin_add_order" else tr(uid, "enter_employee_id")
        await message.answer(prompt, reply_markup=admin_keyboard(uid))
        return
    action = pending_action.get(uid)
    if action == "admin_add_order":
        code = text.strip().upper()
        if not code or len(code) > 64:
            await message.answer(tr(uid, "new_order"), reply_markup=admin_keyboard(uid))
            return
        now = datetime.now(timezone.utc).isoformat()
        try:
            with db() as con:
                con.execute("INSERT INTO orders(code,status,updated_at,updated_by) VALUES(?,0,?,?)", (code, now, uid))
                con.execute("INSERT INTO order_history(code,status,changed_at,changed_by) VALUES(?,0,?,?)", (code, now, uid))
            pending_action.pop(uid, None)
            await message.answer(tr(uid, "created", code=code), reply_markup=admin_keyboard(uid))
        except sqlite3.IntegrityError:
            pending_action.pop(uid, None)
            await message.answer(tr(uid, "exists"), reply_markup=admin_keyboard(uid))
        return
    if action in ("admin_add_employee", "admin_remove_employee"):
        if not text.isdigit():
            await message.answer(tr(uid, "bad_id"), reply_markup=admin_keyboard(uid))
            return
        employee_id = int(text)
        with db() as con:
            if action == "admin_add_employee":
                con.execute("INSERT OR IGNORE INTO employees(user_id,added_at) VALUES(?,?)", (employee_id, datetime.now(timezone.utc).isoformat()))
                response = tr(uid, "employee_added", uid=employee_id)
            else:
                con.execute("DELETE FROM employees WHERE user_id=?", (employee_id,))
                response = tr(uid, "employee_removed", uid=employee_id)
        pending_action.pop(uid, None)
        await message.answer(response, reply_markup=admin_keyboard(uid))
        return
    if isinstance(action, tuple) and action[0] == "staff_status":
        code = action[1]
        status = next((i for i in range(STATUS_COUNT) if text == f"{STATUS_ICONS[i]} {status_name(get_lang(uid), i)}"), None)
        if status is not None:
            now = datetime.now(timezone.utc).isoformat()
            with db() as con:
                cur = con.execute("UPDATE orders SET status=?,updated_at=?,updated_by=? WHERE code=?", (status, now, uid, code))
                if cur.rowcount:
                    con.execute("INSERT INTO order_history(code,status,changed_at,changed_by) VALUES(?,?,?,?)", (code, status, now, uid))
            pending_action.pop(uid, None)
            await message.answer(tr(uid, "updated", code=code, status=status_name(get_lang(uid), status)), reply_markup=main_keyboard(uid))
            return
        await message.answer(tr(uid, "choose_status", code=code), reply_markup=order_status_keyboard(code, get_lang(uid)))
        return
    if action in ("track", "staff_search"):
        code = text.upper()
        with db() as con:
            row = con.execute("SELECT code,status,updated_at FROM orders WHERE code=?", (code,)).fetchone()
        pending_action.pop(uid, None)
        if not row:
            await message.answer(tr(uid, "not_found"), reply_markup=main_keyboard(uid))
            return
        updated = row["updated_at"].replace("T", " ")[:19] + " UTC"
        await message.answer(tr(uid, "order", code=row["code"], status=status_name(get_lang(uid), row["status"]), updated=updated))
        if action == "staff_search":
            pending_action[uid] = ("staff_status", code)
            await message.answer(tr(uid, "choose_status", code=code), reply_markup=order_status_keyboard(code, get_lang(uid)))
        else:
            await message.answer(tr(uid, "menu"), reply_markup=main_keyboard(uid))
        return
    await message.answer(tr(uid, "menu"), reply_markup=main_keyboard(uid))

@dp.callback_query(F.data.startswith("set:"))
async def set_status(callback: CallbackQuery, bot: Bot):
    uid = callback.from_user.id
    if not is_employee(uid):
        await callback.answer(tr(uid, "no_access"), show_alert=True)
        return
    try:
        _, code, status_s = callback.data.split(":")
        status = int(status_s)
        if not (0 <= status < STATUS_COUNT):
            raise ValueError
    except ValueError:
        await callback.answer("Invalid status", show_alert=True)
        return
    now = datetime.now(timezone.utc).isoformat()
    with db() as con:
        cur = con.execute("UPDATE orders SET status=?,updated_at=?,updated_by=? WHERE code=?", (status, now, uid, code))
        if cur.rowcount:
            con.execute("INSERT INTO order_history(code,status,changed_at,changed_by) VALUES(?,?,?,?)", (code, status, now, uid))
    if cur.rowcount:
        await callback.message.edit_text(tr(uid, "updated", code=code, status=status_name(get_lang(uid), status)))
        await callback.answer("OK")
    else:
        await callback.answer(tr(uid, "not_found"), show_alert=True)

async def main():
    init_db()
    bot = Bot(TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
