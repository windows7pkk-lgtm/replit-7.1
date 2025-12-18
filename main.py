# -*- coding: utf-8 -*-
# main.py (CODE YOZUCHI @cryosky) PAPKA [replit] 
import os
import asyncio
import random
import json
import uuid
import signal
import time
from aiogram.utils.markdown import escape_md
import html
from aiogram.dispatcher.middlewares import BaseMiddleware
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext  # <--- QOSILDI
from aiogram.dispatcher.filters.state import State, StatesGroup # <--- QOSILDI
from aiogram.contrib.fsm_storage.memory import MemoryStorage # <--- QOSILDI
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils import executor
from database import (
    init_db, add_user, get_user_count, get_kino_by_code,
    get_all_codes, delete_kino_code, get_code_stat,
    increment_stat, get_all_user_ids, get_today_users,
    add_anime, get_all_admins, add_admin, remove_admin,
    search_anime_by_name, get_conn, update_anime_code, update_anime_poster,
    add_channel_to_db, get_channels_by_type, delete_channel_from_db,
    set_bot_active, get_bot_active, ban_user, unban_user,
    is_user_banned, get_all_banned_users, add_multiple_users,
    add_part_to_anime, delete_part_from_anime,
    get_user_profile, update_user_balance, set_user_balance,
    give_vip, remove_vip, is_user_vip, get_all_vip_users,
    get_vip_prices, update_vip_price, get_card_number, set_card_number,
    add_payment_request, get_pending_payment_requests, approve_payment_request,
    reject_payment_request, get_all_genres, get_anime_by_genre, get_random_anime,
    get_top_anime, update_anime_genre, set_anime_forward_status, get_anime_forward_status,
    update_user_activity, get_active_today_users, get_weekly_new_users,
        get_all_vip_user_ids, get_all_regular_user_ids, get_full_stat_data, 
    add_pending_request, is_request_pending, remove_all_pending_requests, get_all_anime_list_for_ai, 
    log_ai_action, clean_old_logs, get_full_database_dump, restore_database_from_dump, date_converter
)



PID_FILE = "bot_id.pid"

def restart_system():
    if os.path.isfile(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            print("Eski bot ochirildi.")
        except:
            pass
    
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    print("Yangi bot ishga tushdi!")

restart_system()

# --- PID САҚЛАШ (ЯНГИ) ---
pid = os.getpid()
with open('pid.txt', 'w') as f:
    f.write(str(pid))
print(f"[BOT START] PID: {pid} | {datetime.now()}")
# --- ТУГАДИ ---

import logging
from threading import Thread
try:
    from web_app import run_flask_app
    FLASK_AVAILABLE = True
except ImportError:
    print("⚠️ Ескерту: web_app.py файлы табылмады немесе қате бар. Веб-сервер іске қосылмайды.")
    run_flask_app = None
    FLASK_AVAILABLE = False
# --- (MEN QOSDIM) YANGI AI IMPORT (KLASSIK) ---
try:
    # Klassik, eng barqaror paket nomini ishlatamiz
    import google.generativeai as genai
    print("[AI] 'google-generativeai' kutubxonasi topildi.")

    # genai.GenerativeModel ni ishlatish uchun to'g'ridan-to'g'ri chaqirish shart emas
    # chunki u genai moduli ichida bo'ladi
except ImportError:
    print("XATOLIK: 'google-generativeai' kutubxonasi topilmadi. Uni o'rnating: python3.11 -m pip install google-generativeai")
    genai = None
# --- (MEN QOSDIM) TUGADI ---


load_dotenv()

# --- (MEN QOSDIM) YANGI AI SOZLAMALARI (KLASSIK USUL) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_AVAILABLE = False
ai_model = None

if GEMINI_API_KEY and genai:
    try:
        # Klassik SDK usuli: genai.configure() orqali API kalitini o'rnatamiz
        genai.configure(api_key=GEMINI_API_KEY)

        # Modelni to'g'ridan-to'g'ri model nomi bilan yaratamiz
        ai_model = genai.GenerativeModel('gemini-2.5-flash')

        print("[AI] Gemini AI muvaffaqiyatli sozlandi (Flash 2.5 modeli).")
        AI_AVAILABLE = True
    except Exception as e:
        # Barcha xatoliklarni ushlaymiz
        print(f"[AI XATOLIK] Gemini sozlashda xatolik: {e}")
        AI_AVAILABLE = False
else:
    if not genai:
        print("[AI OGOHLANTIRISH] 'google-generativeai' kutubxonasi yuklanmadi.")
    if not GEMINI_API_KEY:
        print("[AI OGOHLANTIRISH] .env faylda GEMINI_API_KEY topilmadi. AI funksiyalari o'chirilgan.")
# --- (MEN QOSDIM) AI SOZLAMALARI TUGADI ---

#keep_alive()

API_TOKEN = os.getenv("API_TOKEN")
CHANNELS = []
LINKS = []
CHANNEL_USERNAMES = []
MAIN_CHANNELS = []
MAIN_LINKS = []
MAIN_USERNAMES = []
BOT_USERNAME = os.getenv("BOT_USERNAME")

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage) # <-QOSILDI

admin_env = os.getenv("ADMIN_IDS", "")
START_ADMINS = []

if admin_env:
    try:
        START_ADMINS = [int(x.strip()) for x in admin_env.split(",") if x.strip().isdigit()]
    except Exception as e:
        print(f"Xatolik ADMIN_IDS o'qishda: {e}")

ADMINS = set(START_ADMINS)

# Bu sizning kodingizda bo'lishi kerak (user_data)
user_data = {}
# AI кутіп тұрған әрекеттерді сақтайтын орын
ai_pending_actions = {}
#AQLILI AI UCHUN OZI BOT NI BOSHQARADI
ai_ignore_list = {}

class AIState(StatesGroup):
    chat_mode = State()       # AI bilan suhbat rejimi
    waiting_video = State()   # Anime videosini kutish rejimi
    vip_assist = State()
async def load_channels():
    global CHANNELS, LINKS, CHANNEL_USERNAMES, MAIN_CHANNELS, MAIN_LINKS, MAIN_USERNAMES
    sub_channels = await get_channels_by_type('sub')
    CHANNELS = [ch[0] for ch in sub_channels]
    LINKS = [ch[1] for ch in sub_channels]
    CHANNEL_USERNAMES = [ch[2] if len(ch) > 2 else "" for ch in sub_channels]

    main_channels = await get_channels_by_type('main')
    MAIN_CHANNELS = [ch[0] for ch in main_channels]
    MAIN_LINKS = [ch[1] for ch in main_channels]
    MAIN_USERNAMES = [ch[2] if len(ch) > 2 else "" for ch in main_channels]

# --- KEYBOARDS (O'ZGARTIRILGAN) ---

def user_panel_keyboard(is_admin=False, is_vip=False): # is_vip параметрі қосылды
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🔍 Anime izlash"), KeyboardButton("🎞 Barcha animelar"))
    
    if is_vip:
        # VIP үшін арнайы түймелер
        kb.add(KeyboardButton("💳 Pul kiritish"), KeyboardButton("👤 Profil"))
    else:
        # Қарапайым қолданушылар үшін
        kb.add(KeyboardButton("💳 Pul kiritish"), KeyboardButton("👤 Profil"))
        
    kb.add(KeyboardButton("📦 Buyurtma berish"), KeyboardButton("💎 VIP olish"))
    kb.add(KeyboardButton("✉️ Admin bilan bog'lanish"))
    
    if is_admin:
        kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb

def admin_panel_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    kb.add(KeyboardButton("📡 Kanal boshqaruvi"))

    kb.add(KeyboardButton("📄 Kodlar ro'yxati"), KeyboardButton("🎬 Anime yuklash"))


    kb.add(KeyboardButton("📊 Statistika"), KeyboardButton("👥 Adminlar"))


    kb.add(KeyboardButton("✉️ Xabar yuborish"), KeyboardButton("📤 Post qilish"))

    kb.add(KeyboardButton("📋 Kodlar paneli"), KeyboardButton("🤖 Bot paneli"))

    kb.add(KeyboardButton("👤 Foydalanuvchi paneli"), KeyboardButton("🌐 Anime sayti"))  # <

    return kb

def anime_sozlash_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🎬 Anime yuklash"), KeyboardButton("➕ Qism qo'shish"))
    kb.add(KeyboardButton("📋 Animelar ro'yxati"), KeyboardButton("🔙 Admin paneli"))
    return kb

def kodlar_panel_keyboard():
    # '📄 Kodlar ro'yxati' olib tashlandi
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("❌ Kodni o'chirish"), KeyboardButton("🔄 Kodni tahrirlash"))
    kb.add(KeyboardButton("📈 Kod statistikasi"), KeyboardButton("✏️ Postni tahrirlash"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def bot_panel_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🤖 Bot holati"), KeyboardButton("👥 User qo'shish"))
    kb.add(KeyboardButton("💎 VIP boshqaruvi"), KeyboardButton("🎬 Anime statusi"))
    # --- ЖАҢА БАТЫРМАЛАР ---
    kb.add(KeyboardButton("📥 Baza olish"), KeyboardButton("📤 Baza yuklash"))
    # -----------------------
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def anime_search_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("📝 Nomi bilan izlash"), KeyboardButton("🔢 Kodi bilan izlash"))
    kb.add(KeyboardButton("🎭 Janr orqali izlash"), KeyboardButton("🎲 Tasodifiy animelar"))
    kb.add(KeyboardButton("🏆 10 TOP animelar"), KeyboardButton("🌐 Anime sayti"))  # <
    kb.add(KeyboardButton("🔙 Orqaga"))
    return kb
    # ... (қалған батырмалар) ...

def vip_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("💎 VIP ga nima kiradi?"), KeyboardButton("💰 VIP sotib olish"))
    kb.add(KeyboardButton("🔙 Orqaga"))
    return kb


def vip_management_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("➕ VIP berish"), KeyboardButton("❌ VIP olish"))
    kb.add(KeyboardButton("💳 Karta boshqaruvi"), KeyboardButton("💵 Pul qo'shish"))
    kb.add(KeyboardButton("💸 Pul olish"), KeyboardButton("💰 VIP narxini belgilash"))
    kb.add(KeyboardButton("📋 VIP userlar ro'yxati"), KeyboardButton("💳 To'lov so'rovlari"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def back_keyboard():
    # Bu faqat foydalanuvchi menyulari uchun
    return ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga")

def admin_back_keyboard():
    # Bu faqat admin menyulari uchun
    return ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Admin paneli")


def admin_menu_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Admin qo'shish")
    kb.add("➖ Admin o'chirish")
    kb.add("👥 Adminlar ro'yxati")
    kb.add("🔙 Admin paneli")
    return kb


def bot_status_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("✅ Botni yoqish"), KeyboardButton(" ⛔️ Botni o'chirish"))
    kb.add(KeyboardButton("🚫 User ban qilish"), KeyboardButton("✅ User ban dan chiqarish"))
    kb.add(KeyboardButton("📋 Banlangan userlar"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def edit_code_menu_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🔄 Nomini o'zgartirish"))
    kb.add(KeyboardButton("➕ Qisim qo'shish"), KeyboardButton("➖ Qisim o'chirish"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb

# YANGI KEYBOARD (Xabar yuborish uchun)
def admin_broadcast_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("👤 Bitta foydalanuvchiga"))
    kb.add(KeyboardButton("👥 Barcha foydalanuvchilarga"))
    kb.add(KeyboardButton("💎 VIP foydalanuvchilarga"))
    kb.add(KeyboardButton("⭐️ Oddiy foydalanuvchilarga"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb

# --- END KEYBOARDS ---

def anime_parts_selector_keyboard(code, current_part=1, total_parts=1):
    """
    Qismlarni tanlash uchun keyboard (ТҮЗЕТІЛГЕН: Шектеу алынды)
    """
    # row_width=5 дегеніміз бір қатарда 5 түйме болады
    kb = InlineKeyboardMarkup(row_width=5)
    
    buttons = []
    # min(total_parts, 10) ЕМЕС, жай ғана total_parts қолданамыз
    for i in range(1, total_parts + 1):
        if i == current_part:
            btn_text = f"✅ {i}"  # Hozirgi qism yashil
        else:
            btn_text = f"{i}"
        buttons.append(InlineKeyboardButton(btn_text, callback_data=f"select_part:{code}:{i}"))
    
    # Барлық түймелерді қосамыз (aiogram өзі 5-тен бөледі)
    kb.add(*buttons)
    
    # Астына жүктеу түймесін қосамыз
    kb.row(
        InlineKeyboardButton("📥 Tez yuklash (Barchasi)", callback_data=f"download_all:{code}")
    )
    
    return kb

# --- YANGI FUNKSIYA (Post qilish uchun kanal tanlash menyusi)
async def generate_channel_selection_keyboard(user_id, code): # <-- 1. 'code' ҚОСЫЛДЫ
    """
    Foydalanuvchi uchun kanal tanlash menyusini yaratadi.
    user_data da 'selected_channels' (set) bo'lishi kerak.
    """
    data = user_data.get(user_id, {})
    selected_channels = data.get('selected_channels', set())

    kb = InlineKeyboardMarkup(row_width=1)

    # Barcha asosiy kanallarni tugma sifatida qo'shamiz
    for idx, channel_id in enumerate(MAIN_CHANNELS):
        # ... (name, display_name logic)
        name = MAIN_USERNAMES[idx]
        display_name = f"@{name}" if name else f"ID: {channel_id}"

        if channel_id in selected_channels:
            button_text = f"✅ {display_name}"
        else:
            button_text = f"☑️ {display_name}"
        # ... (if/else tugaydi)

        # 2. 'code' БАРЛЫҚ ЖЕРГЕ ҚОСЫЛДЫ:
        kb.add(InlineKeyboardButton(button_text, callback_data=f"post_toggle_ch:{channel_id}:{code}"))

    # Boshqaruv tugmalari
    kb.add(InlineKeyboardButton("✅ Barchasiga jo'natish", callback_data=f"post_send_all:{code}"))

    selected_count = len(selected_channels)
    kb.add(InlineKeyboardButton(f"🚀 Jo'natish ({selected_count} ta tanlangan)", callback_data=f"post_send_selected:{code}"))

    kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=f"post_cancel:{code}"))

    return kb

# --- END (Yangi funksiya) ---


async def get_unsubscribed_channels(user_id):
    is_vip = await is_user_vip(user_id)
    if is_vip or user_id in ADMINS:
        return []

    unsubscribed = []
    for idx, channel_id in enumerate(CHANNELS):
        try:
            member = await bot.get_chat_member(channel_id, user_id)

            # 1. Егер пайдаланушы канал мүшесі БОЛМАСА
            if member.status not in ["member", "administrator", "creator"]:
                # 2. Базадан "сұраныс" (заявка) бар-жоғын тексереміз
                is_pending = await is_request_pending(user_id, channel_id)

                # 3. Егер мүше болмаса ЖӘНЕ сұранысы да жоқ болса, тізімге қосамыз
                if not is_pending:
                    unsubscribed.append((channel_id, LINKS[idx]))
        except:
            # Каналда қате болса да (мысалы, бот бан алса), базаны тексереміз
            is_pending = await is_request_pending(user_id, channel_id)
            if not is_pending:
                unsubscribed.append((channel_id, LINKS[idx]))
    return unsubscribed

async def make_unsubscribed_markup(user_id, code):
    unsubscribed = await get_unsubscribed_channels(user_id)
    markup = InlineKeyboardMarkup(row_width=1)
    for channel_id, channel_link in unsubscribed:
        try:
            chat = await bot.get_chat(channel_id)
            markup.add(InlineKeyboardButton(f"➕ {chat.title}", url=channel_link))
        except:
            pass
    markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data=f"checksub:{code}"))
    return markup


# --- POST FORMAT (O'ZGARTIRILGAN) ---
#--- CHANEL POSTI BOSHLANDI---
#--- SEND CHANEL POST.---
async def send_channel_post(channel_id, kino, code):
    title = escape_md(kino.get('title', 'Noma\'lum'))
    parts_count = kino.get('post_count', 0)
    genre = escape_md(kino.get('genre', 'Anime'))
    ovoz_berdi = escape_md(kino.get('ovoz_berdi', ''))
    
    # --- ТҮЗЕТУ БАСТАЛДЫ (Канал логикасы) ---
    # Пост жіберіліп жатқан нақты каналдың username-ін іздейміз
    current_username = ""
    
    # Егер channel_id біздің MAIN_CHANNELS тізімінде болса
    if channel_id in MAIN_CHANNELS:
        try:
            # ID арқылы индексті тауып, сол индекстегі username-ді аламыз
            idx = MAIN_CHANNELS.index(channel_id)
            if idx < len(MAIN_USERNAMES):
                current_username = MAIN_USERNAMES[idx]
        except:
            pass
            
    # Егер тізімнен табылмаса немесе бос болса, default қоямыз
    if not current_username:
        current_username = "animelar_serveri" # Default username
        
    channel_username = escape_md(current_username)
    # --- ТҮЗЕТУ АЯҚТАЛДЫ ---

    caption = "✽ ──...──:•°⛩°•:──...──╮\n"
    caption += f"    ✨ {title} ✨\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"
    caption += f"🎞 Qismlar soni : {parts_count}\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🖋 Janri : {genre}\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"

    if ovoz_berdi:
        caption += f"🎙 Ovoz berdi : {ovoz_berdi}\n"
        caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"

    caption += "💭 Tili : O'zbek\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🔍 Kod : {code}\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    # Түзетілген username осында қойылады
    caption += f"🌐 Manzil: @{channel_username}"

    button_text = kino.get('button_text') or "💎 Tomosha qilish 💎"
    button_url = kino.get('button_url') or f"https://t.me/{BOT_USERNAME}?start={code}"

    download_btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton(button_text, url=button_url)
    )

    try:
        media_type = kino.get('media_type', 'photo')
        if media_type == "photo":
            await bot.send_photo(channel_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        elif media_type == "video":
            await bot.send_video(channel_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        else:
            await bot.send_document(channel_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
    except Exception as e:
        print(f"Xatolik kanalga post yuborishda ({channel_id}): {e}")
        # raise  <-- Қате болса тоқтап қалмау үшін алып тастауға болады, немесе қалдырыңыз
#--- END CHANEL POST
#--- REKLAMA POSTI BOSHLANDI---
#--- SEND REKLAMA POST---

async def send_reklama_post(user_id, code):
    kino = await get_kino_by_code(code)
    if not kino:
        await bot.send_message(user_id, "❌ Kod topilmadi.")
        return

    title = escape_md(kino.get('title', 'Noma\'lum'))
    parts_count = kino.get('post_count', 0)
    genre = escape_md(kino.get('genre', 'Anime'))
    ovoz_berdi = escape_md(kino.get('ovoz_berdi', ''))  # Ovoz berdi maydoni
    channel_username = escape_md(MAIN_USERNAMES[0] if MAIN_USERNAMES else "@animelar_serveri")

    caption = "✽ ──...──:•°⛩°•:──...──╮\n"
    caption += f"    ✨ {title} ✨\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"
    caption += f"🎞 Qismlar soni : {parts_count}\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🖋 Janri : {genre}\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"

    if ovoz_berdi:
        caption += f"🎙 Ovoz berdi : {ovoz_berdi}\n"
        caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"

    caption += "💭 Tili : O'zbek\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🔍 Kod : {code}\n"  # Qidirish soni орнына Kod қосылды
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🌐 Manzil: @{channel_username}"

    bot_me = await bot.get_me()
    url_link = f"https://t.me/{bot_me.username}?start={code}"

    button_text = "🎬 Tomosha qilish"

    # Callback емес, URL қолданамыз!
    download_btn = InlineKeyboardMarkup().add(
         InlineKeyboardButton(button_text, url=url_link)
     )

    try:
        media_type = kino.get('media_type', 'photo')
        if media_type == "photo":
            await bot.send_photo(user_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        elif media_type == "video":
            await bot.send_video(user_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        else:
            await bot.send_document(user_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")

        await increment_stat(code, "viewed")  # Viewed санын жаңарту
    except Exception as e:
        await bot.send_message(user_id, f"❌ Xatolik yuz berdi: {e}")

# --- END POST FORMAT ---
#SEND ANIME PARTS

# main.py ішіндегі send_anime_parts функциясын ауыстыр:
async def send_anime_parts(user_id, code):
    kino = await get_kino_by_code(code)
    if not kino:
        await bot.send_message(user_id, "❌ Anime kodi topilmadi.")
        return

    title = kino.get('title', 'Noma\'lum')
    parts = kino.get('parts_file_ids', [])
    forward_is_enabled = kino.get('forward_enabled', True)
    protect_status = not forward_is_enabled

    success_count = 0
    failure_count = 0

    await bot.send_message(user_id, f"🎬 <b>{title}</b> animesining {len(parts)} ta qismi yuborilmoqda. Iltimos, kuting...", parse_mode="HTML")

    for idx, file_id in enumerate(parts, 1):
        try:
            # 1. DOCUMENT ретінде жіберуге тырысамыз (Ең қауіпсізі)
            await bot.send_document(
                user_id,
                file_id,
                caption=f"📂 {title} - {idx}-qism",
                protect_content=protect_status
            )
            success_count += 1
            await asyncio.sleep(0.2) # Telegram rate-limit-тен сақтану үшін
            
        except Exception as e_doc:
            # 2. DOCUMENT қате кетсе, VIDEO ретінде жіберуге тырысамыз
            try:
                await bot.send_video(
                    user_id,
                    file_id,
                    caption=f"📂 {title} - {idx}-qism",
                    protect_content=protect_status
                )
                success_count += 1
                await asyncio.sleep(0.2)
            except Exception as e_vid:
                failure_count += 1
                # 3. Егер екеуі де қате кетсе, админге хабарлаймыз
                print(f"[ERROR] {code} kodi ({idx}-qism) yuborishda xatolik: DOC: {e_doc} | VID: {e_vid}")
                
                # Админге жеке хабарлама жібереміз
                try:
                    await bot.send_message(
                        user_id,
                        f"⚠️ **{idx}-QISM YUBORILMADI!**\n\n"
                        f"Sabab: {str(e_vid)[:150]}\n"
                        f"Ehtimol: Fayl topilmadi yoki judda katta.",
                        parse_mode="Markdown"
                    )
                except:
                    pass

    # Нәтижені юзерге жібереміз
    if failure_count > 0:
        await bot.send_message(
            user_id,
            f"❌ Xatolik yuz berdi! {failure_count} ta qism yuborilmadi. Iltimos, admin bilan bog'laning."
        )
    else:
        await bot.send_message(
            user_id,
            f"✅ Barcha {success_count} ta qism muvaffaqiyatli yuborildi. Rahmat!"
        )

#SEND ANIME PARTS TUGADI
@dp.message_handler(commands=['start'], state="*")
async def start_handler(message: types.Message, state: FSMContext):
    """
    /start buyrug'i uchun to'liq handler.
    Foydalanuvchi holatini tozalaydi va qaytadan ishga tushiradi.
    """
    # 0. Егер қолданушы қандай да бір процесте тұрса (кино күту, файл күту), оны тоқтатамыз
    await state.finish()

    # 1. Userni bazaga saqlash
    uid = message.from_user.id
    # TÜZETU: 'db.add_user' емес, тікелей 'add_user' шақырамыз
    await add_user(uid, message.from_user.full_name, message.from_user.username)

    # 2. Ban tekshirish
    if await is_user_banned(uid):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    # 3. Bot aktivligini tekshirish
    bot_active = await get_bot_active()
    if not bot_active and uid not in ADMINS:
        await message.answer("🚫 Bot hozirda vaqtincha to'xtatilgan.")
        return

    # ... (start_handler басы өзгеріссіз қалады) ...

    # 4. DEEP LINK (KOD BILAN KIRISH) - ЕҢ БІРІНШІ ТҰРУ КЕРЕК!
    args = message.get_args()
    if args and args.isdigit():
        code = args
        await increment_stat(code, "init")
        await increment_stat(code, "searched")

        unsubscribed = await get_unsubscribed_channels(uid)
        if unsubscribed:
            markup = await make_unsubscribed_markup(uid, code)
            await message.answer("❗ Animeni olishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
        else: 
            await send_episode_message(uid, code, part_num=1) 
        return

    # 5. KODSIZ KIRISH (ODDIY /start) - OBUNA TEKSHIRISH
    unsubscribed = await get_unsubscribed_channels(uid)
    if unsubscribed:
        markup = await make_unsubscribed_markup(uid, "start")
        await message.answer("❗ Botdan foydalanishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
        return 

    # 6. ROLGA QARAB BO'LISH

    # --- A) AGAR ADMIN BO'LSA ---
    if uid in ADMINS:
        await message.answer(
            f"👑 <b>Xush kelibsiz, Ho'jayin {message.from_user.first_name}!</b>\n\n"
            "Bugun nima qilamiz?",
            reply_markup=admin_panel_keyboard(), # Admin panel ochiladi
            parse_mode="HTML"
        )
        return

    # --- B) AGAR VIP YOKI ODDIY USER BO'LSA ---
    is_vip = False
    try:
        is_vip = await is_user_vip(uid)
    except:
        is_vip = False

    if is_vip:
        # VIP MATNI (Siz bergan matn o'згеріссіз қалды)
        welcome_text = (
            "💎 <b>Assalomu alaykum!</b>\n\n"
            f"⭐ <b>{message.from_user.first_name}</b>, VIP foydalanuvchi!\n\n"
            "🎬 Bu yerda o'zingizga kerakli bo'lgan animeni topishingiz mumkin!\n"
            "AI xizmatidan foydalanish mumkin!\n"
            "✨ VIP sifatida siz barcha imkoniyatlardan foydalana olasiz!\n\n"
            "🔥 <b>Qiziqarli anime dunyosiga xush kelibsiz!</b>" 
        )
        # VIP menyu
        await message.answer(welcome_text, reply_markup=user_panel_keyboard(is_vip=True), parse_mode="HTML")
    else:
        # ODDIY USER MATNI (Siz bergan matn o'згеріссіз қалды)
        welcome_text = (
             "🎭 <b>Assalomu alaykum!</b>\n\n"
            f"👤 <b>{message.from_user.first_name}</b>, botimizga xush kelibsiz!\n\n"
            "🎬 Bu yerda yuzlab anime qismlarni topishingiz mumkin!\n"
            "🔍 Qidirish orqali o'zingizga yoqqan animeni toping!\n\n"
            "✨ <b>Qiziqarli anime dunyosiga xush kelibsiz!</b>"
        )
        # Oddiy menyu
        await message.answer(welcome_text, reply_markup=user_panel_keyboard(is_vip=False), parse_mode="HTML")

# --- ЖАҢА ФУНКЦИЯ: БІР БӨЛІМДІ ТҮЙМЕЛЕРМЕН ЖІБЕРУ ---
async def send_episode_message(user_id, code, part_num=1):
    kino = await get_kino_by_code(code)
    if not kino:
        await bot.send_message(user_id, "❌ Anime topilmadi.")
        return

    parts_list = kino.get('parts_file_ids', [])
    total_parts = len(parts_list)

    if total_parts == 0:
        await bot.send_message(user_id, "❌ Hozircha qismlar yuklanmagan.")
        return

    if part_num < 1 or part_num > total_parts:
        await bot.send_message(user_id, "❌ Bu qism mavjud emas.")
        return

    # Файлды аламыз
    file_id = parts_list[part_num-1]
    title = kino.get('title', 'Noma\'lum')
    
    # Түймелерді жасаймыз (1, 2, 3... және Tez yuklash)
    kb = anime_parts_selector_keyboard(code, part_num, total_parts)
    
    caption = f"🎬 <b>{title}</b>\n💿 {part_num}-qism\n\n🤖 @{BOT_USERNAME}"

    try:
        media_type = kino.get('media_type', 'photo') # Негізгі типті тексереміз, бірақ бөлімдер әдетте видео болады
        
        # Видео ретінде жібереміз
        await bot.send_video(
            user_id, 
            file_id, 
            caption=caption, 
            reply_markup=kb, 
            parse_mode="HTML",
            protect_content=not kino.get('forward_enabled', True)
        )
    except Exception as e:
        # Егер видео болмаса, документ қылып жібереміз
        try:
            await bot.send_document(
                user_id, 
                file_id, 
                caption=caption, 
                reply_markup=kb, 
                parse_mode="HTML",
                protect_content=not kino.get('forward_enabled', True)
            )
        except Exception as e2:
            await bot.send_message(user_id, f"❌ Xatolik: {e2}")

@dp.message_handler(commands=['contact'])
async def contact_command(message: types.Message):
    if await is_user_banned(message.from_user.id):
        user_data[message.from_user.id] = {'action': 'contact_admin'}
        await message.answer("✍️ Adminlarga yubormoqchi bo'lgan xabaringizni yozing.")
    else:
        await message.answer("✉️ Admin bilan bog'lanish uchun menyudan foydalaning.")

# --- ZAYAVKA KANALLARNI AVTO-TASDIQLASH ---

@dp.chat_join_request_handler()
async def handle_join_request(update: types.ChatJoinRequest):
    global CHANNELS  # Global majburiy obuna kanallari ro'yxati

    chat_id = update.chat.id
    user_id = update.from_user.id

    # Bot faqat bizning majburiy obuna (sub) kanallarimiz ro'yxatidagi
    # kanallar uchun so'rovlarni bazaga saqlashi kerak.

    if chat_id in CHANNELS:
        try:
            # Foydalanuvchi so'rovini bazaga saqlaymiz
            await add_pending_request(user_id, chat_id)
            print(f"[ZAYAVKA] Foydalanuvchi {user_id} uchun {chat_id} kanaliga so'rov bazaga saqlandi.")

            # (Ixtiyoriy) Foydalanuvchiga bu haqida xabar berish
            try:
                await bot.send_message(user_id,
                    f"✅ \"{update.chat.title}\" zayafka saqlandi.\n\n"
                    "«✅ Yana tekshirish» tugmasni bosin."
                )
            except Exception as e:
                print(f"Xatolik (zayavka xabari yuborish): {e}")

        except Exception as e:
            print(f"Xatolik (zayavka saqlash): {e}")

# --- END ZAYAVKA HANDLER ---

# --- NAVIGATION HANDLERS (O'ZGARTIRILGAN) ---

@dp.message_handler(lambda m: m.text == "👤 Foydalanuvchi paneli")
async def switch_to_user_panel(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    # Админнің өзі VIP па, жоқ па тексереміз (меню дұрыс шығуы үшін)
    is_vip = False
    try:
        is_vip = await is_user_vip(message.from_user.id)
    except:
        is_vip = False

    # is_vip параметрін қосып, менюді шығарамыз
    await message.answer("👤 Foydalanuvchi paneli:", reply_markup=user_panel_keyboard(is_admin=True, is_vip=is_vip))
# --- SMART ORQAGA QAYTISH (TO'LIQ VA FINAL VERSIYA) ---

@dp.message_handler(lambda m: m.text == "🔙 Orqaga")
async def back_to_main(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Hozirgi holatni tekshiramiz
    data = user_data.get(user_id, {})
    current_action = data.get('action')

    # --- A) AGAR IZLASH MENYUSIDA BO'LSA ---
    # (Bu qismni siz so'ragan edingiz - Izlash menyusiga qaytaradi)
    if current_action in ['search_by_name', 'search_by_code']:
        user_data.pop(user_id, None) # Aniq harakatni o'chiramiz
        await anime_search_menu(message) # Izlash menyusini chiqaramiz
        return

    # --- B) AGAR PUL KIRITISH YOKI BUYURTMA MENYUSIDA BO'LSA ---
    # Bu yerda User Panelga qaytamiz, lekin VIP knopkalarini to'g'ri ko'rsatishimiz kerak
    if current_action in ['payment_upload', 'order_service', 'contact_admin']:
        user_data.pop(user_id, None)
        
        # VIP ekanligini tekshiramiz
        is_vip = False
        try:
            is_vip = await is_user_vip(user_id)
        except:
            is_vip = False
            
        is_admin = user_id in ADMINS
        
        await message.answer("👤 Foydalanuvchi paneli:", reply_markup=user_panel_keyboard(is_admin=is_admin, is_vip=is_vip))
        return

    # --- C) STANDART (BOSHQA BARCHA HOLATLAR) ---
    # Bosh menyuga to'liq qaytish
    user_data.pop(user_id, None) 

    # VIP ekanligini tekshiramiz
    is_vip = False
    try:
        is_vip = await is_user_vip(user_id)
    except:
        is_vip = False

    is_admin = user_id in ADMINS

    await message.answer("👤 Foydalanuvchi paneli:", reply_markup=user_panel_keyboard(is_admin=is_admin, is_vip=is_vip))

# --- ADMIN SMART BACK (MUHIM O'ZGARISH) ---

@dp.message_handler(lambda m: m.text == "🔙 Admin paneli")
async def back_to_admin_panel(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    current_action = data.get('action')

    # 1. KODLAR PANELI ichidagilar -> Kodlar paneliga qaytadi
    if current_action in ['delete_code', 'edit_code_select', 'view_stat', 'edit_post', 'edit_code_menu', 'edit_code_name', 'add_part', 'delete_part']:
        user_data.pop(user_id, None)
        await message.answer("📋 Kodlar paneli:", reply_markup=kodlar_panel_keyboard())
        return

    # 2. BOT PANELI ichidagilar -> Bot paneliga qaytadi
    if current_action in ['ban_user', 'unban_user', 'add_users', 'anime_status_code']:
        user_data.pop(user_id, None)
        await message.answer("🤖 Bot paneli:", reply_markup=bot_panel_keyboard())
        return

    # 3. VIP BOSHQARUVI ichidagilar -> VIP paneliga qaytadi
    if current_action in ['admin_give_vip', 'admin_remove_vip', 'update_card', 'admin_add_balance', 'admin_remove_balance', 'update_vip_price']:
        user_data.pop(user_id, None)
        await message.answer("💎 VIP boshqaruvi:", reply_markup=vip_management_keyboard())
        return
        
    # 4. KANAL BOSHQARUVI (sub/main) -> Kanal menyusiga qaytadi
    if current_action == 'add_channel':
        # Kanal turini (sub/main) saqlab qolamiz, faqat 'add' actionini o'chiramiz
        ctype = data.get('channel_type')
        user_data[user_id] = {'channel_type': ctype} # Faqat tipni qoldiramiz
        
        # Menyuni qayta chizamiz (Inline tugmalar orqali)
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("➕ Kanal qo'shish", callback_data="action:add"),
            InlineKeyboardButton("📋 Kanal ro'yxati", callback_data="action:list")
        )
        kb.add(
            InlineKeyboardButton("❌ Kanal o'chirish", callback_data="action:delete"),
            InlineKeyboardButton("🔙 Orqaga (Admin)", callback_data="action:back_admin")
        )
        text = "📡 Majburiy obuna kanallari menyusi:" if ctype == "sub" else "📌 Asosiy kanallar menyusi:"
        await message.answer(text, reply_markup=kb)
        return

    # 5. STANDART (Bosh admin menyusiga to'liq chiqish)
    user_data.pop(user_id, None)
    await message.answer("👮‍♂️ Admin panel:", reply_markup=admin_panel_keyboard())
# --- END NAVIGATION HANDLERS ---
#  CHEK SUBSCRIBTION

@dp.callback_query_handler(lambda c: c.data.startswith("checksub:"))
async def check_subscription_callback(call: types.CallbackQuery):
    if await is_user_banned(call.from_user.id):
        await call.answer("⛔️ Siz ban qilingan foydalanuvchisiz.", show_alert=True)
        return

    bot_active = await get_bot_active()
    if not bot_active and call.from_user.id not in ADMINS:
        await call.answer("🚫 Bot vaqtincha to'xtatilgan.", show_alert=True)
        return

    code = call.data.split(":")[1]

    # 1. Жазылмаған НЕМЕСЕ сұраныс жібермеген каналдарды аламыз
    # (Біз бұл функцияны өзгерттік, ол енді базаны да тексереді)
    unsubscribed_channels = await get_unsubscribed_channels(call.from_user.id)

    # 2. Нәтижені тексереміз
    if unsubscribed_channels:
        # Егер әлі де сұраныс жіберілмеген каналдар болса
        markup = InlineKeyboardMarkup(row_width=1)
        for channel_id, channel_link in unsubscribed_channels:
            try:
                chat = await bot.get_chat(channel_id)
                markup.add(InlineKeyboardButton(f"➕ {chat.title}", url=channel_link))
            except:
                pass
        markup.add(InlineKeyboardButton("✅ Yana tekshirish", callback_data=f"checksub:{code}"))

        try:
            await call.message.edit_text("❗ Hali ham obuna bo'lmagan yoki сұраныс жіберілмеген kanal(lar):", reply_markup=markup)
        except: # Егер мәтін өзгермеген болса
            pass

        await call.answer(
            "🔄 Tekshirildi. Ro'yxatdagi kanallarga сұраныс (zayavka) yuboring va qaytadan tekshiring.",
            show_alert=True,
            cache_time=1
        )
    else:
            await call.message.delete()

            # --- ЖАҢА ТЕКСЕРУ БАСТАЛДЫ ---
            if code == "start":
                # Бұл /start-тан кейінгі тексеру, аниме жіберудің қажеті жоқ
                # Тек сәлемдесу хабарын жібереміз
                await call.answer("✅ Obuna tasdiqlandi! Botga xush kelibsiz!")

                is_vip = await is_user_vip(call.from_user.id)
                if is_vip:
                    welcome_text = (
                        "💎 Assalomu alaykum!\n\n"
                        f"⭐ {call.from_user.first_name}, VIP foydalanuvchi!\n\n"
                        "🎬 Bu yerda minglab anime seriallarini topishingiz mumkin!\n"
                        "✨ VIP sifatida siz barcha imkoniyatlardan foydalana olasiz!\n\n"
                        "🔥 Qiziqarli anime dunyosiga xush kelibsiz!"
                    )
                else:
                    welcome_text = (
                        "🎭 Assalomu alaykum!\n\n"
                        f"👤 {call.from_user.first_name}, botimizga xush kelibsiz!\n\n"
                        "🎬 Bu yerda minglab anime seriallarini topishingiz mumkin!\n"
                        "🔍 Qidirish orqali o'zingizga yoqqan animeni toping!\n\n"
                        "✨ Qiziqarli anime dunyosiga xush kelibsiz!"
                    )

                if call.from_user.id in ADMINS:
                    await call.message.answer(welcome_text, reply_markup=admin_panel_keyboard())
                else:
                    await call.message.answer(welcome_text, reply_markup=user_panel_keyboard())

            else:
                # Бұл аниме коды бар ескі тексеру
                await send_reklama_post(call.from_user.id, code)
                await increment_stat(code, "searched")
                await call.answer("✅ Obuna tasdiqlandi! Anime yuborilmoqda...")
            # --- ЖАҢА ТЕКСЕРУ АЯҚТАЛДЫ ---

            await remove_all_pending_requests(call.from_user.id) # <-- (Біз мұны 1-қадамда қосқанбыз)

#  --- END CHEK SUB
@dp.callback_query_handler(lambda c: c.data.startswith("download_anime:"))
async def download_anime_callback(call: types.CallbackQuery):
    """
    Tomosha qilish bosilganda: avval postni qayta chiqaramiz, keyin 1-qismni yuboramiz
    """
    code = call.data.split(":")[1]
    kino = await get_kino_by_code(code)
    
    if not kino:
        await call.answer("❌ Anime kodi topilmadi.", show_alert=True)
        return
    
    total_parts = kino.get('post_count', 0)
    if total_parts == 0:
        await call.answer("❌ Bu animeda qismlar yo'q.", show_alert=True)
        return
    
    # 1. POSTNI QAYTA CHIQARAMIZ (reply sifatida)
    await send_reklama_post(call.from_user.id, code)
    
    # 2. 1-QISMNI YUBORAMIZ
    parts_list = kino.get('parts_file_ids', [])
    if parts_list:
        try:
            file_id = parts_list[0]
            title = kino.get('title', 'Noma\'lum')
            await bot.send_document(
                call.from_user.id,
                file_id,
                caption=f"📂 {title} - 1-qism"
            )
        except:
            pass
    
    # 3. MENYUNI YUBORAMIZ (agar 1 dan kop qism bolsa)
    if total_parts > 1:
        kb = anime_parts_selector_keyboard(code, 1, total_parts)
        
        # Faqat menyuni yuboramiz
        title = kino.get('title', 'Noma\'lum')
        caption_text = f"🎬 **{title}**\n\n📦 Jami qismlar: {total_parts} ta\n\n👇 Qaysi qismni yuklab olmoqchisiz?"

        await call.message.answer(
                 caption_text,
                 reply_markup=kb,
                 parse_mode="Markdown"
         )
    
    await call.answer("✅ 1-qism yuborildi!") 

# --- DEEP LINK VA PLAYER LOGIKASI (JETISHMAYOTGAN QISM) -
async def process_deep_link(message: types.Message, code: int):
    """
    Anime kodini qabul qiladi va posterni tugmalar bilan chiqaradi.
    """
    # 1. Obunani tekshiramiz
    if not await check_subscription(message.from_user.id, message):
        return

    # 2. Animeni bazadan olamiz
    anime = await db.get_anime(code)
    if not anime:
        await message.answer("❌ Bunday kodli anime topilmadi.")
        return

    # 3. Tugmalarni yasaymiz
    cnt = anime.get('post_count', 0)
    kb = InlineKeyboardMarkup(row_width=5)
    
    # Qismlar (1, 2, 3...)
    for i in range(1, cnt + 1):
        kb.insert(InlineKeyboardButton(str(i), callback_data=f"select_part:{code}:{i}"))
    
    # "Tez yuklash" tugmasi
    kb.add(InlineKeyboardButton("📥 Tez yuklash (Barchasi)", callback_data=f"download_all:{code}"))
    
    # 4. Matn
    main_ch = await db.get_main_channel_username()
    ch_txt = f"@{main_ch}" if main_ch else ""
    
    caption = (
        f"📺 <b>{anime['title']}</b>\n\n"
        f"🔢 Jami qismlar: {cnt}\n"
        f"🎭 Janr: {anime['genre']}\n"
        f"🗣 Ovoz: {anime['voice']}\n\n"
        f"👇 <b>Kerakli qismni tanlang:</b>\n"
        f"📡 Kanal: {ch_txt}"
    )
    
    # 5. Yuborish
    try:
        if anime.get('media_type') == 'video':
            await message.answer_video(anime['poster_file_id'], caption=caption, reply_markup=kb)
        else:
            await message.answer_photo(anime['poster_file_id'], caption=caption, reply_markup=kb)
    except Exception as e:
        await message.answer(caption, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("select_part:"))
async def select_part_callback(call: types.CallbackQuery):
    parts = call.data.split(":")
    code = parts[1]
    part_num = int(parts[2])
    
    # Жаңа бөлімді жаңа хабарлама етіп жібереміз
    await send_episode_message(call.from_user.id, code, part_num)
    
    # Кнопка басылғанын білдіру үшін (жүктелу дөңгелегін тоқтату)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("download_all:"))
async def download_all_callback(call: types.CallbackQuery):
    """
    "Tez yuklash" bosilganda ishlaydi
    """
    code = call.data.split(":")[1]
    await call.answer("📥 Yuklanmoqda...", show_alert=False)
    # send_anime_parts funksiyasi faylda bor, shuni chaqiramiz
    await send_anime_parts(call.from_user.id, code)
    
@dp.message_handler(lambda m: m.text == "🔍 Anime izlash")
async def anime_search_menu(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    bot_active = await get_bot_active()
    if not bot_active and message.from_user.id not in ADMINS:
        await message.answer("🚫 Bot hozirda vaqtincha to'xtatilgan.")
        return

    # --- ТІРКЕЛУДІ ТЕКСЕРУ ҚОСЫЛДЫ ---
    unsubscribed = await get_unsubscribed_channels(message.from_user.id)
    if unsubscribed:
        # "search_menu" деп арнайы код береміз (оны check_subscription_callback-те өңдеу керек болады)
        markup = await make_unsubscribed_markup(message.from_user.id, "search_menu")
        await message.answer("❗ Bu bo'limga kirish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=markup)
        return
    # ---------------------------------

    await update_user_activity(message.from_user.id)
    await message.answer("🔍 Anime izlash menyusi:", reply_markup=anime_search_menu_keyboard())

@dp.message_handler(lambda m: m.text == "🌐 Anime sayti")
async def open_anime_webapp(message: types.Message):
    site_url = os.getenv("SITE_URL")
    if not site_url:
        await message.answer("Sayt manzili hali sozlanmagan.")
        return

    # Oddiy havola sifatida ochiladi (Telegram tashqarisida)
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Anime saytini ochish",
            url=site_url  # <--- WebApp emas, oddiy URL
        )
    )

    await message.answer(
        "Anime saytiga o‘tish:",
        reply_markup=keyboard
    )

@dp.message_handler(lambda m: m.text == "📝 Nomi bilan izlash")
async def anime_search_by_name(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    user_data[message.from_user.id] = {'action': 'search_by_name'}
    await message.answer("📝 Anime nomini kiriting:\n\nMisol: 'Naruto'", reply_markup=back_keyboard())


@dp.message_handler(lambda m: m.text == "🔢 Kodi bilan izlash")
async def anime_search_by_code(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    user_data[message.from_user.id] = {'action': 'search_by_code'}
    await message.answer("🔢 Anime kodini kiriting:\n\nMisol: '147'", reply_markup=back_keyboard())

#JANR ORQALI IZLASH OZGARDI SANA 2025 11 28

# main.py ішінде

# --- 1. ЖАНРЛАР МӘЗІРІ (Әдемі түймелер) ---
@dp.message_handler(lambda m: m.text == "🎭 Janr orqali izlash")
async def genre_search_menu(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    genres = await get_all_genres()
    if not genres:
        await message.answer("❌ Hozircha janrlar yo'q.")
        return

    # Түймелерді екі-екіден тіземіз
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for genre in genres:
        # Жанр аты тым ұзын болса қысқартамыз
        btn_text = f"🎭 {genre}"
        buttons.append(InlineKeyboardButton(btn_text, callback_data=f"genre:{genre}"))
    
    kb.add(*buttons) # Барлық түймені қосу

    await message.answer("🎭 Kerakli janrni tanlang:", reply_markup=kb)


# --- 2. ТІЗІМ ШЫҒАРУ (Мәтіндік формат) ---
# main.py ішіндегі show_genre_animes функциясын тап және мынаған ауыстыр:

@dp.callback_query_handler(lambda c: c.data.startswith("genre:"))
async def show_genre_animes(call: types.CallbackQuery):
    genre_name = call.data.split(":", 1)[1]
    
    # Осы жанр кездесетін барлық анимелерді іздейміз
    # (database-те get_anime_by_genre функциясы LIKE %genre% қолданады, бұл дұрыс)
    animes = await get_anime_by_genre(genre_name, limit=100)

    if not animes:
        await call.message.answer(f"❌ '{genre_name}' janrida anime topilmadi.")
        await call.answer()
        return

    # Тізімді әдемілеу
    text = f"💎👑--[ - Animelar Ro'yxati - ]--👑💎\n\n"
    text += f"💎👑--[ - Janr: {genre_name.upper()} - ]--👑💎\n\n"

    for anime in animes:
        title = anime.get('title', 'Nomsiz')
        link = f"https://t.me/{BOT_USERNAME}?start={anime['code']}"
        
        # Әр аниме жаңа жолда, жақша ішінде тұрады
        text += f"🔹 [ {title} ]({link})\n" 

    # Хабарлама тым ұзын болса
    if len(text) > 4000:
        text = text[:4000] + "\n... (davomi bor)"

    back_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_genres"))

    await call.message.answer(text, parse_mode="Markdown", reply_markup=back_btn, disable_web_page_preview=True)
    await call.answer()


# --- АРТҚА ҚАЙТУ (Қосымша) ---
@dp.callback_query_handler(lambda c: c.data == "back_to_genres")
async def back_to_genres_callback(call: types.CallbackQuery):
    await call.message.delete()
    await genre_search_menu(call.message)

#JANR ORQALI IZLASH KODI TUGADI

# --- TASODIFIY ANIME (NAVIGATSIYA BILAN - TARIYXIY) ---

@dp.message_handler(lambda m: m.text == "🎲 Tasodifiy animelar")
async def random_anime_start(message: types.Message):
    user_id = message.from_user.id
    if await is_user_banned(user_id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    # 1. Birinchi random animeni olamiz
    random_anime = await get_random_anime(1)
    if not random_anime:
        await message.answer("❌ Hozircha animelar yo'q.")
        return

    code = random_anime[0]['code']

    # 2. Yangi tarix yaratamiz
    user_data[user_id] = {
        'random_history': [code], # Ko'rilganlar ro'yxati
        'history_index': 0        # Hozirgi turgan joyimiz (0-chi element)
    }

    # 3. Ekranga chiqarish
    await show_random_anime_smart(message, user_id, is_new=True)


async def show_random_anime_smart(message_obj, user_id, is_new=False):
    # Ma'lumotlarni olamiz
    data = user_data.get(user_id, {})
    history = data.get('random_history', [])
    index = data.get('history_index', 0)

    if not history:
        await bot.send_message(user_id, "❌ Xatolik. Qaytadan kiring.")
        return

    # Hozirgi kodni olamiz
    current_code = history[index]
    kino = await get_kino_by_code(current_code)
    
    if not kino:
        await bot.send_message(user_id, "❌ Anime topilmadi.")
        return

    title = kino.get('title', 'Noma\'lum')
    genre = kino.get('genre', 'Anime')
    parts_count = kino.get('post_count', 0)
    
    caption = (
        f"🎲 <b>TASODIFIY ANIME</b>\n\n"
        f"📺 <b>{title}</b>\n"
        f"🎭 Janr: {genre}\n"
        f"📦 Qismlar: {parts_count} ta\n"
        f"🔢 Kod: <code>{current_code}</code>"
    )

    # TUGMALARNI SOZLASH
    kb = InlineKeyboardMarkup(row_width=3)
    
    # "Ortga" tugmasi: Agar 0-chi elementda bo'lsak, tugma ishlamasligi kerak (vizual ko'rinaveradi)
    btn_prev = InlineKeyboardButton("⬅️ Orqaga", callback_data="history:prev")
    btn_down = InlineKeyboardButton("📥 Yuklab olish", callback_data=f"download_anime:{current_code}")
    btn_next = InlineKeyboardButton("Oldinga ➡️", callback_data="history:next")

    kb.add(btn_prev, btn_down, btn_next)

    try:
        media_type = kino.get('media_type', 'photo')
        file_id = kino.get('poster_file_id')

        if is_new:
            # Yangi xabar (Menyudan kirganda)
            if media_type == "video":
                await bot.send_video(user_id, file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await bot.send_photo(user_id, file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
        else:
            # Eskisini tahrirlash (Knopka bosganda)
            media = types.InputMediaVideo(media=file_id, caption=caption, parse_mode="HTML") if media_type == 'video' else types.InputMediaPhoto(media=file_id, caption=caption, parse_mode="HTML")
            await message_obj.edit_media(media=media, reply_markup=kb)
            
    except Exception as e:
        # Edit qilib bo'lmasa, yangisini yuboramiz
        if not is_new:
            await message_obj.delete()
            if media_type == "video":
                await bot.send_video(user_id, file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await bot.send_photo(user_id, file_id, caption=caption, reply_markup=kb, parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("history:"))
async def history_navigation_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split(":")[1]
    
    data = user_data.get(user_id, {})
    history = data.get('random_history', [])
    index = data.get('history_index', 0)

    if not history:
        await call.answer("❌ Sessiya eskirgan.", show_alert=True)
        return

    if action == "prev":
        # ARTQA BOSILDI
        if index > 0:
            # Agar orqada anime bor bo'lsa, o'shani ko'rsatamiz
            index -= 1
            user_data[user_id]['history_index'] = index
            await show_random_anime_smart(call.message, user_id, is_new=False)
        else:
            # Agar eng boshida tursa
            await call.answer("⚠️ Bu birinchi anime! Orqaga yo'l yo'q.", show_alert=True)
            return

    elif action == "next":
        # ALGA BOSILDI
        if index < len(history) - 1:
            # Agar tarixta oldinda anime bor bo'lsa (avval ko'rgan bo'lsa), o'shani ko'rsatamiz
            index += 1
            user_data[user_id]['history_index'] = index
            await show_random_anime_smart(call.message, user_id, is_new=False)
        else:
            # Agar tarix tugagan bo'lsa -> YANGI RANDOM olamiz
            new_anime = await get_random_anime(1)
            if new_anime:
                new_code = new_anime[0]['code']
                # Tarixga qo'shamiz
                history.append(new_code)
                index += 1
                
                # Yangilaymiz
                user_data[user_id]['random_history'] = history
                user_data[user_id]['history_index'] = index
                
                await show_random_anime_smart(call.message, user_id, is_new=False)
            else:
                await call.answer("❌ Boshqa anime qolmadi.")
                return

    await call.answer()

@dp.message_handler(lambda m: m.text == "🏆 10 TOP animelar")
async def top_10_animes(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    # VIP-тексеру осы жерден алып тасталды

    top_animes = await get_top_anime(10)
    if not top_animes:
        await message.answer("❌ Hozircha animelar yo'q.")
        return

    text = "🏆 TOP 10 ANIMELAR:\n\n"
    kb = InlineKeyboardMarkup(row_width=1)

    for idx, anime in enumerate(top_animes, 1):
        title = anime.get('title', 'Noma\'lum')
        viewed = anime.get('viewed', 0)
        code = anime.get('code', '')
        text += f"{idx}. 📺 {title} - 👁 {viewed} ko\'rilgan\n"
        kb.add(InlineKeyboardButton(f"{idx}. {title}", callback_data=f"select_anime:{code}"))

    await message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("select_anime:"))
async def select_anime_callback(call: types.CallbackQuery):
    code = call.data.split(":")[1]
    await call.message.delete()

    unsubscribed = await get_unsubscribed_channels(call.from_user.id)
    if unsubscribed:
        markup = await make_unsubscribed_markup(call.from_user.id, code)
        await call.message.answer("❗ Animeni olishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
    else:
        await send_reklama_post(call.from_user.id, code)

    await call.answer()


@dp.message_handler(lambda m: m.text == "🎞 Barcha animelar")
async def show_all_animes(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return

    bot_active = await get_bot_active()
    if not bot_active and message.from_user.id not in ADMINS:
        await message.answer("🚫 Bot hozirda vaqtincha to'xtatilgan.")
        return

    kodlar = await get_all_codes()
    if not kodlar:
        await message.answer("⛔️ Hozircha animelar yo'q.")
        return

    kodlar = sorted(kodlar, key=lambda x: int(x["code"]) if x["code"].isdigit() else float('inf'))
    chunk_size = 100
    for i in range(0, len(kodlar), chunk_size):
        chunk = kodlar[i:i + chunk_size]
        text = "📄 *Barcha animelar:*\n\n"
        for row in chunk:
            text += f"`{row['code']}` – *{row['title']}*\n"
        await message.answer(text, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text == "💳 Pul kiritish")
async def payment_menu(message: types.Message):
    card = await get_card_number()
    user_data[message.from_user.id] = {'action': 'payment_upload'}
    await message.answer(
        f"💳 KARTA RAQAMI:\n\n<code>{card}</code>\n\n"
        "📸 To'lov chekini yuboring:\n\n"
        "⚠️ Iltimos, to'lovni amalga oshiring va chek rasmini yuboring.",
        parse_mode="HTML",
        reply_markup=back_keyboard() # User menyusi
    )


@dp.message_handler(lambda m: m.text == "💎 VIP olish")
async def vip_menu(message: types.Message):
    await message.answer("💎 VIP menyusi:", reply_markup=vip_menu_keyboard())


@dp.message_handler(lambda m: m.text == "💎 VIP ga nima kiradi?")
async def vip_info(message: types.Message):
    await message.answer(
        "💎 VIP IMKONIYATLARI:\n\n"
        "✅ Reklama yo'q\n"
        "✅ Kanal obunasiz yuklab olish\n"
        "✅ Janr bo'yicha qidirish\n"
        "✅ Tasodifiy anime tanlash\n"
        "✅ TOP animelarni ko'rish\n"
        "✅ Yangi animelar haqida xabardor bo'lish\n\n"
        "🔥 VIP bo'ling va barcha imkoniyatlardan bahramand bo'ling!"
    )


@dp.message_handler(lambda m: m.text == "💰 VIP sotib olish")
async def buy_vip_menu(message: types.Message):
    prices = await get_vip_prices()

    kb = InlineKeyboardMarkup(row_width=1)
    for tariff, info in prices.items():
        price = info['price']
        days = info['days']
        tariff_name = {
            '1month': '1 oylik',
            '3month': '3 oylik',
            '6month': '6 oylik'
        }.get(tariff, tariff)
        kb.add(InlineKeyboardButton(f"💎 {tariff_name} - {price:,} so'm", callback_data=f"buy_vip:{tariff}"))

    await message.answer(
        "💎 VIP TARIFLAR:\n\n"
        "Kerakli tarifni tanlang:",
        reply_markup=kb
    )


# main.py (VIP SATIB OLISH - AVTOMATIK BALANSDAN)
@dp.callback_query_handler(lambda c: c.data.startswith("buy_vip:"))
async def buy_vip_callback(call: types.CallbackQuery):
    tariff = call.data.split(":")[1]
    prices = await get_vip_prices()

    if tariff not in prices:
        await call.answer("❌ Xatolik: Tarif topilmadi.", show_alert=True)
        return

    price = prices[tariff]['price']
    days = prices[tariff]['days']
    user_id = call.from_user.id

    # 1. User balansini tekshiramiz
    profile = await get_user_profile(user_id)
    current_balance = profile.get('balance', 0)

    if current_balance >= price:
        # 2. Pul yetarli bo'lsa -> Yechib olamiz va VIP beramiz
        new_balance = current_balance - price
        
        # Balansdan ayirish
        await update_user_balance(user_id, -price)
        # VIP berish
        await give_vip(user_id, days)
        
        await call.message.delete()
        await call.message.answer(
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"✅ Siz {days} kunlik VIP sotib oldingiz!\n"
            f"💰 Hisobingizdan {price:,} so'm yechildi.\n"
            f"💎 Hozirgi balans: {new_balance:,} so'm.\n\n"
            f"Endi <b>🤖 AI Yordamchi</b> va boshqa imkoniyatlar ochildi! /start ni bosing.",
            parse_mode="HTML",
            # is_vip=True деп береміз, себебі ол жаңа ғана сатып алды
            reply_markup=user_panel_keyboard(is_admin=(user_id in ADMINS), is_vip=True)
        )
        
        # Adminlarga xabar (Log)
        for admin_id in ADMINS:
            try:
                await bot.send_message(admin_id, f"💰 <b>Yangi savdo!</b>\nUser: {user_id}\nTarif: {tariff}\nSumma: {price}")
            except: pass
            
    else:
        # 3. Pul yetmasa -> To'lov qilishga undaymiz
        diff = price - current_balance
        await call.answer(f"❌ Mablag' yetarli emas! Yana {diff:,} so'm kerak.", show_alert=True)
        await call.message.answer(
            f"❌ <b>Mablag' yetarli emas!</b>\n\n"
            f"Sizning balansingiz: {current_balance:,} so'm\n"
            f"Tarif narxi: {price:,} so'm\n\n"
            f"💳 Iltimos, avval hisobingizni to'ldiring:",
            reply_markup=user_panel_keyboard()
        )

@dp.message_handler(lambda m: m.text == "📦 Buyurtma berish")
async def order_service(message: types.Message):
    user_data[message.from_user.id] = {'action': 'order_service'}
    await message.answer(
        "📦 BUYURTMA BERISH\n\n"
        "Qanday anime yoki xizmat kerakligini yozing.\n"
        "Admin siz bilan bog'lanadi!",
        reply_markup=back_keyboard() # User menyusi
    )


@dp.message_handler(lambda m: m.text == "👤 Profil")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    profile = await get_user_profile(user_id)

    balance = profile.get('balance', 0)
    is_vip = profile.get('is_vip', False)
    vip_until = profile.get('vip_until')
    vip_count = profile.get('vip_count', 0)

    vip_status = "💎 VIP" if is_vip else "⭐ Oddiy"
    vip_info = ""

    if is_vip and vip_until:
        vip_info = f"\n⏳ VIP tugaydi: {vip_until.strftime('%d.%m.%Y')}"

    await message.answer(
        f"👤 PROFIL\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👨‍💼 Ism: {message.from_user.full_name}\n"
        f"📊 Status: {vip_status}{vip_info}\n"
        f"💰 Balans: {balance:,} so'm\n"
        f"🔢 VIP xaridlar: {vip_count} marta",
        parse_mode="HTML"
    )


@dp.message_handler(lambda m: m.text == "✉️ Admin bilan bog'lanish")
async def contact_admin(message: types.Message):
    user_data[message.from_user.id] = {'action': 'contact_admin'}
    await message.answer(
        "✉️ ADMIN BILAN BOG'LANISH\n\n"
        "Xabaringizni yozing, admin javob beradi:",
        reply_markup=back_keyboard() # User menyusi
    )


@dp.callback_query_handler(lambda c: c.data.startswith("reply_user:"))
async def reply_user_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return

    target_user = int(call.data.split(":")[1])
    user_data[call.from_user.id] = {'action': 'reply_to_user', 'target_user': target_user}

    await call.message.answer(
        f"✍️ Foydalanuvchiga javob yozish: {target_user}\n\n"
        "Xabaringizni yozing:",
        reply_markup=admin_back_keyboard() # Admin menyusi
    )
    await call.answer()

# --- ADMIN HANDLERS (O'ZGARTIRILGAN) ---

# --- BAZA OLISH VA YUKLASH (BACKUP SYSTEM) ---

@dp.message_handler(lambda m: m.text == "📥 Baza olish")
async def export_database(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    wait_msg = await message.answer("⏳ Baza yuklanmoqda... Iltimos kuting.")
    
    try:
        # 1. Bazadan ma'lumotlarni olamiz
        data = await get_full_database_dump()
        
        # 2. Fayl nomini yaratamiz (sana bilan)
        filename = f"backup_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.json"
        
        # 3. JSON faylga yozamiz
        with open(filename, "w", encoding="utf-8") as f:
            # date_converter datetime obyektlarni matnga aylantiradi
            json.dump(data, f, indent=4, default=date_converter, ensure_ascii=False)
            
        # 4. Faylni adminga yuboramiz
        with open(filename, "rb") as f:
            await bot.send_document(
                message.chat.id, 
                f, 
                caption=f"📦 <b>To'liq Baza nusxasi</b>\n📅 Sana: {datetime.now()}\n👥 Userlar: {len(data['users'])}\n🎬 Animelar: {len(data['kino_codes'])}"
            )
            
        # 5. Faylni o'chirib tashlaymiz (server to'lmasligi uchun)
        os.remove(filename)
        await wait_msg.delete()
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")


@dp.message_handler(lambda m: m.text == "📤 Baza yuklash")
async def import_database_ask(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    user_data[message.from_user.id] = {'action': 'upload_db'}
    await message.answer(
        "📂 <b>Baza faylini yuklash</b>\n\n"
        "Menga <code>.json</code> formatidagi backup faylini yuboring.\n"
        "Yoki shunchaki ID lar ro'yxati bo'lsa ham bo'ladi.\n\n"
        "<i>Eslatma: Bu amal eski ma'lumotlarni yangilaydi!</i>",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard()
    )

# Faylni qabul qilish
@dp.message_handler(content_types=types.ContentTypes.DOCUMENT)
async def process_database_upload(message: types.Message):
    # Agar admin baza yuklash rejimida bo'lmasa, qaytaramiz
    if message.from_user.id not in ADMINS:
        return
    
    data_state = user_data.get(message.from_user.id, {})
    if data_state.get('action') != 'upload_db':
        return

    # JSON ekanligini tekshiramiz
    if not message.document.file_name.endswith('.json'):
        await message.answer("❌ Iltimos, faqat .json fayl yuboring!")
        return

    wait_msg = await message.answer("⏳ Fayl o'qilmoqda va bazaga yozilmoqda...")

    try:
        # 1. Faylni yuklab olish
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Vaqtincha nom
        temp_name = f"import_{message.from_user.id}.json"
        await bot.download_file(file_path, temp_name)
        
        # 2. O'qish
        with open(temp_name, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
        # 3. Agar bu shunchaki ID lar ro'yxati bo'lsa (Siz aytgan variant)
        # Misol fayl: [12345, 67890, ...]
        if isinstance(db_data, list) and all(isinstance(x, int) for x in db_data):
            # Uni bizning formatga o'tkazamiz
            db_data = {"users": db_data}
            
        # 4. Bazaga tiklash
        await restore_database_from_dump(db_data)
        
        # 5. Tozalash
        os.remove(temp_name)
        user_data.pop(message.from_user.id, None)
        
        await wait_msg.edit_text("✅ <b>Baza muvaffaqiyatli tiklandi!</b>\n\nBarcha ma'lumotlar yangilandi.")
        
    except Exception as e:
        if os.path.exists(temp_name): os.remove(temp_name)
        await wait_msg.edit_text(f"❌ Xatolik: {e}")

@dp.message_handler(lambda m: m.text == "📋 Kodlar paneli")
async def kodlar_panel_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("📋 Kodlar paneli:", reply_markup=kodlar_panel_keyboard())


@dp.message_handler(lambda m: m.text == "🤖 Bot paneli")
async def bot_panel_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("🤖 Bot paneli:", reply_markup=bot_panel_keyboard())


@dp.message_handler(lambda m: m.text == "📡 Kanal boshqaruvi")
async def channel_management(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📢 Majburiy obuna", callback_data="channel_type:sub"),
        InlineKeyboardButton("📌 Asosiy kanallar", callback_data="channel_type:main")
    )

    await message.answer("📡 Kanal boshqaruvi:", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("channel_type:"))
async def select_channel_type(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ctype = callback.data.split(":")[1]
    user_data[callback.from_user.id] = {'channel_type': ctype}

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ Kanal qo'shish", callback_data="action:add"),
        InlineKeyboardButton("📋 Kanal ro'yxati", callback_data="action:list")
    )
    kb.add(
        InlineKeyboardButton("❌ Kanal o'chirish", callback_data="action:delete"),
        InlineKeyboardButton("🔙 Orqaga (Admin)", callback_data="action:back_admin")
    )

    text = "📡 Majburiy obuna kanallari menyusi:" if ctype == "sub" else "📌 Asosiy kanallar menyusi:"
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("action:"))
async def channel_actions(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    action = callback.data.split(":")[1]
    data = user_data.get(callback.from_user.id, {})
    ctype = data.get("channel_type")

    if not ctype and action != "back_admin":
        await callback.answer("❗ Avval kanal turini tanlang.")
        return

    if action == "add":
        user_data[callback.from_user.id] = {'action': 'add_channel', 'channel_type': ctype, 'step': 'id'}
        await callback.message.answer("🆔 Kanal ID yuboring (masalan: -1001234567890):", reply_markup=admin_back_keyboard())

    elif action == "list":
        await load_channels()
        if ctype == "sub":
            channels = list(zip(CHANNELS, LINKS, CHANNEL_USERNAMES))
            title = "📋 Majburiy obuna kanallari:\n\n"
        else:
            channels = list(zip(MAIN_CHANNELS, MAIN_LINKS, MAIN_USERNAMES))
            title = "📌 Asosiy kanallar:\n\n"

        if not channels:
            await callback.message.answer("📭 Hali kanal yo'q.")
        else:
            text = title
            for i, (cid, link, username) in enumerate(channels, 1):
                text += f"{i}. 🆔 {cid}\n   🔗 {link}\n"
                if username:
                    text += f"   👤 @{username}\n"
                text += "\n"
            await callback.message.answer(text)

    elif action == "delete":
        await load_channels()
        if ctype == "sub":
            channels = list(zip(CHANNELS, LINKS))
            prefix = "del_sub"
        else:
            channels = list(zip(MAIN_CHANNELS, MAIN_LINKS))
            prefix = "del_main"

        if not channels:
            await callback.message.answer("📭 Hali kanal yo'q.")
            return

        kb = InlineKeyboardMarkup()
        for cid, link in channels:
            kb.add(InlineKeyboardButton(f"O'chirish: {cid}", callback_data=f"{prefix}:{cid}"))
        await callback.message.answer("❌ Qaysi kanalni o'chirmoqchisiz?", reply_markup=kb)

    elif action == "back_admin":
        # Inline menyudan Admin paneliga qaytish
        user_data.pop(callback.from_user.id, None)
        await callback.message.delete()
        await callback.message.answer("👮‍♂️ Admin panel:", reply_markup=admin_panel_keyboard())

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("del_sub:") or c.data.startswith("del_main:"))
async def delete_channel_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    parts = callback.data.split(":")
    prefix = parts[0]
    channel_id = int(parts[1])

    if prefix == "del_sub":
        await delete_channel_from_db(channel_id, 'sub')
        await load_channels()
        await callback.message.answer("✅ Majburiy obuna kanali o'chirildi!")
    else:
        await delete_channel_from_db(channel_id, 'main')
        await load_channels()
        await callback.message.answer("✅ Asosiy kanal o'chirildi!")

    await callback.answer()


@dp.message_handler(lambda m: m.text == "❌ Kodni o'chirish")
async def ask_delete_code(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'delete_code'}
    await message.answer("🗑 Qaysi kodni o'chirmoqchisiz? Kodni yuboring.", reply_markup=admin_back_keyboard())


# 1. Anime sozlash менюін ашу
@dp.message_handler(lambda m: m.text == "⚙️ Anime sozlash")
async def anime_sozlash_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("⚙️ Anime sozlash bo'limi:", reply_markup=anime_sozlash_keyboard())

# 2. Anime yuklash (Жаңа аниме қосу)
@dp.message_handler(lambda m: m.text == "🎬 Anime yuklash")
async def start_add_anime_new(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_anime', 'step': 'code'}
    await message.answer("📝 Yangi anime uchun KOD kiriting:", reply_markup=admin_back_keyboard())

# 3. Qism qo'shish (Бар анимеге бөлім қосу)
@dp.message_handler(lambda m: m.text == "➕ Qism qo'shish")
async def start_add_part_new(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    # Бұл жерде action='start_add_part_flow' деп белгілейміз, код сұрау үшін
    user_data[message.from_user.id] = {'action': 'start_add_part_flow'}
    await message.answer("🔢 Qism qo'shmoqchi bo'lgan animening KODINI yozing:", reply_markup=admin_back_keyboard())

# 4. Тізімді шығару
@dp.message_handler(lambda m: m.text == "📋 Animelar ro'yxati")
async def show_all_codes_new(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    # Бұрынғы show_all_codes_admin функциясын шақырамыз немесе кодын осында жазамыз
    kodlar = await get_all_codes()
    if not kodlar:
        await message.answer("⛔️ Hozircha animelar yo'q.")
        return

    kodlar = sorted(kodlar, key=lambda x: int(x["code"]) if x["code"].isdigit() else float('inf'))
    chunk_size = 50
    for i in range(0, len(kodlar), chunk_size):
        chunk = kodlar[i:i + chunk_size]
        text = "📋 *Animelar ro'yxati:*\n\n"
        for row in chunk:
            text += f"`{row['code']}` – {row['title']}\n"
        await message.answer(text, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text == "➕ Anime qo'shish")
async def start_add_anime(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_anime', 'step': 'code'}
    await message.answer("📝 Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "🔄 Kodni tahrirlash")
async def start_edit_code(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'edit_code_select'}
    await message.answer("📝 Qaysi kodni tahrirlamoqchisiz? Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "✏️ Postni tahrirlash")
async def start_edit_post(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'edit_post', 'step': 'code'}
    await message.answer("📝 Qaysi anime postini tahrirlamoqchisiz? Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "📄 Kodlar ro'yxati")
async def show_all_codes_admin(message: types.Message):
    # Bu endi asosiy admin panelidan chaqiriladi
    if message.from_user.id not in ADMINS:
        return
    kodlar = await get_all_codes()
    if not kodlar:
        await message.answer("⛔️ Hozircha kodlar yo'q.")
        return

    kodlar = sorted(kodlar, key=lambda x: int(x["code"]) if x["code"].isdigit() else float('inf'))

    chunk_size = 100
    for i in range(0, len(kodlar), chunk_size):
        chunk = kodlar[i:i + chunk_size]
        text = "📄 *Kodlar ro'yxati:*\n\n"
        for row in chunk:
            text += f"`{row['code']}` – {row['title']}\n"
        await message.answer(text, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text == "📈 Kod statistikasi")
async def ask_stat_code(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'view_stat'}
    await message.answer("📝 Qaysi kod statistikasini ko'rmoqchisiz? Kodni kiriting:", reply_markup=admin_back_keyboard())


# --- YANGILANGAN STATISTIKA HANDLERI ---
@dp.message_handler(lambda message: message.text == "📊 Statistika")
async def show_full_statistics(message: types.Message):
    # # Admin ekanligini tekshirish
    if message.from_user.id not in ADMINS:
        return

    # # Ping o'lchashni boshlash
    start_time = time.time()
    
    # # Ma'lumotlarni bazadan olish
    stats = await get_full_stat_data()
    
    # # Ping hisoblash (ms)
    end_time = time.time()
    ping = int((end_time - start_time) * 1000)

    # # Bot holati matni
    bot_status = "✅ Yoqilgan" if stats['bot_active'] else "🔴 O'chirilgan"

    # # Javob matnini tayyorlash
    text = (
        f"📊 <b>BOT STATISTIKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']}\n\n"
        
        f"🆕 <b>Bugungi yangi:</b> +{stats['new_today']}\n"
        f"🟢 <b>Bugungi aktiv:</b> {stats['active_today']}\n\n"
        
        f"📅 <b>1 haftalik yangi:</b> +{stats['new_week']}\n"
        f"📈 <b>1 haftalik aktiv:</b> {stats['active_week']}\n\n"
        
        f"📅 <b>30 kunlik yangi:</b> +{stats['new_month']}\n"
        f"📈 <b>30 kunlik aktiv:</b> {stats['active_month']}\n\n"
        
        f"🎬 <b>Jami animelar:</b> {stats['total_anime']} ta\n"
        f"⚡️ <b>Bot pingi:</b> {ping} ms\n"
        f"🤖 <b>Bot holati:</b> {bot_status}"
    )

    await message.answer(text, parse_mode="HTML")
    
from aiogram.dispatcher.middlewares import BaseMiddleware
from database import update_user_activity  # database.py-dan import qilinganiga ishonch hosil qiling

# --- MIDDLEWARE (DIQQAT: SHEGINISLARGA QARANG) ---
class ActivityMiddleware(BaseMiddleware):
    # DIQQAT: Bu qator "class" so'zidan 4 ta bo'sh joy (probel) o'ngda turishi shart!
    async def on_process_message(self, message: types.Message, data: dict):
        if message.from_user:
            await update_user_activity(message.from_user.id)

    # Bu qator ham xuddi shunday surilgan bo'lishi kerak
    async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
        if call.from_user:
            await update_user_activity(call.from_user.id)
            
@dp.message_handler(lambda m: m.text == "👥 Adminlar")
async def admin_management(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("👥 Admin boshqaruvi:", reply_markup=admin_menu_keyboard())


@dp.message_handler(lambda m: m.text == "➕ Admin qo'shish")
async def ask_add_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_admin'}
    await message.answer("👤 Yangi admin ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➖ Admin o'chirish")
async def ask_remove_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'remove_admin'}
    await message.answer("👤 O'chirish kerak bo'lgan admin ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "👥 Adminlar ro'yxati")
async def list_admins(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    admins = await get_all_admins()
    text = "👥 <b>Adminlar ro'yxati:</b>\n\n"
    for admin_id in admins:
        text += f"• <code>{admin_id}</code>\n"
    await message.answer(text, parse_mode="HTML")

# --- BROADCAST (O'ZGARTIRILGAN) ---

# --- BROADCAST (O'ZGARTIRILGAN) ---

# --- КҮШЕЙТІЛГЕН BROADCAST ФУНКЦИЯСЫ (Kod 4-nusqa) ---
async def background_broadcast(message: types.Message, users: list, broadcast_info: dict):
    """
    Kod 3-nusqa: Flood control + Progress Bar + Final Report
    """
    success = 0
    fail = 0
    total_users = len(users)

    BATCH_SIZE = 15   # 15 адам сайын жаңарту
    BATCH_DELAY = 1   # 1 секунд күту
    PER_USER_DELAY = 0.05 

    admin_id = message.chat.id
    
    # Канал username немесе ID және Post ID
    from_chat_id = broadcast_info.get('from_chat_id') 
    message_id = broadcast_info.get('message_id')

    # Жіберу функциясы
    async def send_func(user_id):
        retries = 0
        while retries < 5:
            try:
                # Forward (Бағыттау) жасаймыз
                await bot.forward_message(chat_id=user_id, from_chat_id=from_chat_id, message_id=message_id)
                return True
            except Exception as e:
                err = str(e).lower()
                if "flood" in err or "retry in" in err:
                    try:
                        wait_time = int(err.split("retry in ")[-1].split(" ")[0])
                        await asyncio.sleep(wait_time + 1)
                        retries += 1
                    except:
                        await asyncio.sleep(5)
                        retries += 1
                # Бот блокталған болса немесе чат табылмаса
                elif "blocked" in err or "user is deactivated" in err or "chat not found" in err:
                    return False
                else:
                    return False
        return False

    # 1. Басталуы туралы хабар (Бұны өзгертіп отырамыз)
    status_msg = await bot.send_message(
        admin_id,
        f"🚀 **Xabar yuborish boshlandi!**\n📊 Jami foydalanuvchilar: {total_users}",
        parse_mode="Markdown"
    )

    start_time = time.time()

    # 2. Негізгі цикл
    for i in range(0, total_users, BATCH_SIZE):
        batch = users[i:i+BATCH_SIZE]
        
        for user_id in batch:
            if user_id == admin_id: 
                continue
                
            ok = await send_func(user_id)
            if ok:
                success += 1
            else:
                fail += 1
            await asyncio.sleep(PER_USER_DELAY)

        # Telegram серверін шаршатпау үшін күтеміз
        await asyncio.sleep(BATCH_DELAY)

        # Прогрессті есептейміз
        processed = i + len(batch)
        remaining = total_users - processed
        if remaining < 0: remaining = 0
        
        # Пайызбен көрсету (әдемі болу үшін)
        percent = int((processed / total_users) * 100)
        
        try:
            # ТҮЗЕТУ: Мұнда keyboard ҚОСПАЙМЫЗ (тек мәтін өзгереді)
            await status_msg.edit_text(
                f"🔄 <b>Jarayon ketmoqda... {percent}%</b>\n\n"
                f"✅ Yuborildi: {success}\n"
                f"❌ O'xshamadi: {fail}\n"
                f"⏳ Qoldi: {remaining}\n"
                f"📊 Jami: {total_users}",
                parse_mode="HTML"
            )
        except:
            pass 

    duration = round(time.time() - start_time, 1)

    # 3. АЯҚТАЛҒАН СОҢ (БІТТІ)
    # Ескі "процесс" хабарын өшіріп тастаймыз (немесе сол күйі қалдырсаңыз да болады)
    try:
        await status_msg.delete()
    except:
        pass

    # Нәтижені ЖАҢА хабарлама қылып жібереміз (Сонда Admin Panel кнопкасы шығады)
    await bot.send_message(
        admin_id,
        f"✅ <b>Xabar yuborish muvaffaqiyatli yakunlandi!</b>\n\n"
        f"👥 Jami userlar: {total_users}\n"
        f"✅ Yetib bordi: {success} ta\n"
        f"❌ Yetib bormadi: {fail} ta\n"
        f"⏱ Vaqt: {duration} soniya",
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard() # <--- МІНЕ, ЕНДІ БҰЛ ЖЕРДЕ ҚАТЕ БЕРМЕЙДІ
    )

@dp.message_handler(lambda m: m.text == "✉️ Xabar yuborish")
async def start_broadcast_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Kimga xabar yubormoqchisiz?", reply_markup=admin_broadcast_menu_keyboard())


@dp.message_handler(lambda m: m.text == "👤 Bitta foydalanuvchiga")
async def broadcast_single_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'broadcast_single_id'}
    await message.answer("👤 Foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())

# --- ЖАҢАРТЫЛҒАН BROADCAST HANDLERS ---

@dp.message_handler(lambda m: m.text == "👥 Barcha foydalanuvchilarga")
async def broadcast_all_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await show_broadcast_type_menu(message.from_user.id, 'all')

@dp.message_handler(lambda m: m.text == "💎 VIP foydalanuvchilarga")
async def broadcast_vip_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await show_broadcast_type_menu(message.from_user.id, 'vip')

@dp.message_handler(lambda m: m.text == "⭐️ Oddiy foydalanuvchilarga")
async def broadcast_regular_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await show_broadcast_type_menu(message.from_user.id, 'regular')
# --- END BROADCAST ---

@dp.message_handler(lambda m: m.text == "📤 Post qilish")
async def start_post_process(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'post_to_channel'}
    await message.answer("🔢 Qaysi anime KODini kanalga yubormoqchisiz?\nMasalan: `147`", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "🤖 Bot holati")
async def bot_status_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    bot_active = await get_bot_active()
    status = "✅ Yoqilgan" if bot_active else "⛔️ O'chirilgan"
    await message.answer(f"🤖 Bot holati: {status}\n\nKerakli amalni tanlang:", reply_markup=bot_status_keyboard())


@dp.message_handler(lambda m: m.text == "✅ Botni yoqish")
async def turn_bot_on(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await set_bot_active(True)
    await message.answer("✅ Bot yoqildi! Barcha foydalanuvchilar botdan foydalanishi mumkin.", reply_markup=admin_panel_keyboard())


@dp.message_handler(lambda m: m.text == "⛔️ Botni o'chirish")
async def turn_bot_off(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await set_bot_active(False)
    await message.answer("⛔️ Bot o'chirildi! Faqat adminlar botdan foydalanishi mumkin.", reply_markup=admin_panel_keyboard())


@dp.message_handler(lambda m: m.text == "🚫 User ban qilish")
async def ask_ban_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'ban_user'}
    await message.answer("👤 Ban qilish kerak bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "✅ User ban dan chiqarish")
async def ask_unban_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'unban_user'}
    await message.answer("👤 Ban dan chiqarish kerak bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "📋 Banlangan userlar")
async def show_banned_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    banned = await get_all_banned_users()
    if not banned:
        await message.answer("✅ Hozircha banlangan foydalanuvchilar yo'q.")
        return

    text = "📋 <b>Banlangan foydalanuvchilar:</b>\n\n"
    for user in banned:
        reason = user['reason'] or "Sabab ko'rsatilmagan"
        text += f"👤 ID: <code>{user['user_id']}</code>\n📝 Sabab: {reason}\n\n"
    await message.answer(text, parse_mode="HTML")


@dp.message_handler(lambda m: m.text == "👥 User qo'shish")
async def ask_add_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_users'}
    await message.answer(
        "👥 Foydalanuvchi ID larini yuboring.\n\n"
        "📝 Har bir ID ni yangi qatorda yuboring.\n"
        "⚠️ Maksimal 2500 ta ID qo'shishingiz mumkin.\n\n"
        "Misol:\n123456789\n987654321\n555666777",
        reply_markup=admin_back_keyboard()
    )


@dp.message_handler(lambda m: m.text == "💎 VIP boshqaruvi")
async def vip_management_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("💎 VIP boshqaruvi:", reply_markup=vip_management_keyboard())


@dp.message_handler(lambda m: m.text == "➕ VIP berish")
async def ask_give_vip(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_give_vip', 'step': 'user_id'}
    await message.answer("👤 VIP bermoqchi bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "❌ VIP olish")
async def ask_remove_vip_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_remove_vip'}
    await message.answer("👤 VIP ni olib tashlamoqchi bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "💳 Karta boshqaruvi")
async def ask_card_number(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'update_card'}
    current_card = await get_card_number()
    await message.answer(
        f"💳 Joriy karta raqami:\n<code>{current_card}</code>\n\n"
        "📝 Yangi karta raqamini kiriting:",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard()
    )


@dp.message_handler(lambda m: m.text == "💵 Pul qo'shish")
async def ask_add_balance(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_add_balance', 'step': 'user_id'}
    await message.answer("👤 Foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "💸 Pul olish")
async def ask_remove_balance(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_remove_balance', 'step': 'user_id'}
    await message.answer("👤 Foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "💰 VIP narxini belgilash")
async def ask_vip_price(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1 oylik", callback_data="set_price:1month"),
        InlineKeyboardButton("3 oylik", callback_data="set_price:3month"),
        InlineKeyboardButton("6 oylik", callback_data="set_price:6month")
    )

    await message.answer("💰 Qaysi tarif narxini o'zgartirmoqchisiz?", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("set_price:"))
async def set_vip_price_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return

    tariff = call.data.split(":")[1]
    user_data[call.from_user.id] = {'action': 'update_vip_price', 'tariff': tariff}

    tariff_names = {'1month': '1 oylik', '3month': '3 oylik', '6month': '6 oylik'}
    await call.message.answer(
        f"💰 {tariff_names.get(tariff, tariff)} tarifi uchun yangi narxni kiriting (so'mda):",
        reply_markup=admin_back_keyboard()
    )
    await call.answer()


@dp.message_handler(lambda m: m.text == "📋 VIP userlar ro'yxati")
async def list_vip_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    vip_users = await get_all_vip_users()
    if not vip_users:
        await message.answer("❌ Hozircha VIP foydalanuvchilar yo'q.")
        return

    text = "💎 <b>VIP FOYDALANUVCHILAR:</b>\n\n"
    for user in vip_users:
        vip_until = user['vip_until'].strftime('%d.%m.%Y')
        text += f"👤 ID: <code>{user['user_id']}</code>\n⏳ Tugaydi: {vip_until}\n\n"

    await message.answer(text, parse_mode="HTML")


@dp.message_handler(lambda m: m.text == "💳 To'lov so'rovlari")
async def show_payment_requests(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    requests = await get_pending_payment_requests()
    if not requests:
        await message.answer("✅ Hozircha to'lov so'rovlari yo'q.")
        return

    await message.answer(f"💳 {len(requests)} ta to'lov so'rovi mavjud:")

    for req in requests:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_pay:{req['id']}:{req['user_id']}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_pay:{req['id']}")
        )

        await bot.send_photo(
            message.chat.id,
            req['photo_file_id'],
            caption=f"👤 User ID: <code>{req['user_id']}</code>\n📅 Sana: {req['created_at'].strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML",
            reply_markup=kb
        )


@dp.callback_query_handler(lambda c: c.data.startswith("approve_pay:"))
async def approve_payment_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return

    parts = call.data.split(":")
    request_id = int(parts[1])
    user_id = int(parts[2])

    user_data[call.from_user.id] = {
        'action': 'approve_payment_amount',
        'request_id': request_id,
        'user_id': user_id
    }

    await call.message.answer(
        f"💰 Qancha pul qo'shmoqchisiz? (so'mda)\n\n"
        f"👤 User ID: {user_id}",
        reply_markup=admin_back_keyboard()
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("reject_pay:"))
async def reject_payment_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return

    request_id = int(call.data.split(":")[1])
    await reject_payment_request(request_id)

    await call.message.edit_caption(
        caption=call.message.caption + "\n\n❌ RAD ETILDI",
        parse_mode="HTML"
    )
    await call.answer("❌ To'lov rad etildi!")


@dp.message_handler(lambda m: m.text == "🎬 Anime statusi")
async def anime_status_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'anime_status_code'}
    await message.answer(
        "🎬 ANIME FORWARD STATUSINI BOSHQARISH\n\n"
        "📝 Anime kodini kiriting:",
        reply_markup=admin_back_keyboard()
    )


@dp.message_handler(lambda m: m.text == "🔄 Nomini o'zgartirish")
async def edit_code_name(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    data = user_data.get(message.from_user.id, {})
    if data.get('action') != 'edit_code_menu':
        return
    user_data[message.from_user.id] = {'action': 'edit_code_name', 'code': data.get('code'), 'step': 'new_code'}
    await message.answer("📝 Yangi kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➕ Qisim qo'shish")
async def add_part_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    data = user_data.get(message.from_user.id, {})
    if data.get('action') != 'edit_code_menu':
        return
    user_data[message.from_user.id] = {'action': 'add_part', 'code': data.get('code')}
    await message.answer("📂 Qo'shmoqchi bo'lgan qism (video/fayl) ni yuboring:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➖ Qisim o'chirish")
async def delete_part_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    data = user_data.get(message.from_user.id, {})
    if data.get('action') != 'edit_code_menu':
        return
    code = data.get('code')
    kino = await get_kino_by_code(code)
    if not kino:
        await message.answer("❌ Kod topilmadi.")
        return

    parts_count = kino.get('post_count', 0)
    if parts_count == 0:
        await message.answer("❌ Bu kodda qismlar yo'q.")
        return

    user_data[message.from_user.id] = {'action': 'delete_part', 'code': code}
    await message.answer(
        f"📂 Jami {parts_count} ta qism mavjud.\n\n"
        "🔢 O'chirmoqchi bo'lgan qism raqamini kiriting (masalan: 1, 2, 3...):",
        reply_markup=admin_back_keyboard()
    )

# --- BOSHQA XABARLAR UCHUN HANDLER (O'ZGARTIRILGAN) ---

# --- (MEN QOSDIM) YANGI AI HANDLER (KUCHAYTIRILGAN) ---

# --- (MEN QOSDIM) YANGI AI HANDLER (GOD MODE - 17 FUNKSIYA) ---

# --- GLOBAL AI HISTORY (Suhbat tarixi) ---
# --- GLOBAL AI HISTORY (Suhbat tarixi) ---

ai_sessions = {} # {user_id: [message_history]}

@dp.message_handler(commands=['off'], state='*')
async def stop_ai_mode(message: types.Message, state: FSMContext):
    """
    /off - AI chat rejimini yoki har qanday jarayonni to'xtatish.
    """
    if message.from_user.id not in ADMINS:
        return

    current_state = await state.get_state()
    if current_state:
        await state.finish()
        # Tarixni tozalaymiz
        ai_sessions.pop(message.from_user.id, None)
        await message.answer("🛑 AI Chat rejimi to'xtatildi. Xotira tozalandi.")
    else:
        await message.answer("⚠️ Chat rejimi allaqachon o'chiq.")


# 2. AI KIRISH BUYRUG'I (/ai)
@dp.message_handler(commands=['ai'])
async def ai_entry_handler(message: types.Message, state: FSMContext):
    """
    /ai - Chat rejimini yoqish
    /ai [matn] - Bir martalik buyruq
    """
    if message.from_user.id not in ADMINS:
        return

    args = message.get_args()

    # Agar argument bo'lmasa -> CHAT REJIMINI YOQAMIZ
    if not args:
        await AIState.chat_mode.set()
        ai_sessions[message.from_user.id] = [] # Yangi tarix
        await message.answer(
            "🤖 **AI CHAT REJIMI (ALL-IN-ONE)**\n\n"
            "Men bilan suhbatlashing yoki buyruq bering!\n"
            "Imkoniyatlar:\n"
            "⏰ Postni keyinga qoldirish\n"
            "📥 Anime qo'shish (Auto)\n"
            "💎 VIP, Ban, Statistika va boshqalar...\n\n"
            "To'xtatish uchun: `/off`"
        )
        return

    # Agar argument bo'lsa -> BIR MARTALIK BUYRUQ
    await process_ai_command(message, args, state)
    
# --- AI CHAT REJIMIDAGI XABARLARNI USHLASH ---

# --- AI CHAT REJIMIDAGI XABARLARNI USHLASH ---
@dp.message_handler(state=AIState.chat_mode, content_types=types.ContentTypes.ANY)
async def ai_chat_loop(message: types.Message, state: FSMContext):
    if message.text and message.text.startswith('/ai'):
        return 

    user_id = message.from_user.id
    user_text = message.text or message.caption or "(Rasm/Video)"
    
    # Tarixga yozish
    history = ai_sessions.get(user_id, [])
    history.append(f"Admin: {user_text}")
    
    # Kontekst (Oxirgi 10 xabar)
    context_str = "\n".join(history[-10:])

    # AI ga yuborish
    await process_ai_command(message, user_text, state, context=context_str)


# main.py (AI - ULTIMATE ADMIN CONTROL / NO TOKEN LIMITS)

async def process_ai_command(message: types.Message, prompt_text: str, state: FSMContext, context: str = ""):
    if not AI_AVAILABLE:
        await message.answer("❌ AI sozlanmagan.")
        return

    # Userga vizual javob
    loading = await message.answer("🧠 Buyruq to'liq tahlil qilinmoqda (ULTIMATE AI MODE)...")

    try:
        # Bazadan barcha kerakli ma'lumotlarni yig'amiz (AI qaror qabul qilishi uchun)
        total_users = await get_user_count()
        today_users = await get_today_users()
        vip_users = len(await get_all_vip_users())
        pending_payments = await get_pending_payment_requests()
        pending_count = len(pending_payments)
        bot_status = await get_bot_active()
        all_animes = await get_all_anime_list_for_ai()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # --- SYSTEM PROMPT (BARCHA-BARCHASI QAMRAB OLINGAN) ---
        system_prompt = f"""
Siz - "Animelar Olami" botining DAHOSISIZ (Genius AI).
Hozirda siz ishlavotkan bot nomi anilordtvbot bu botni maqsati odam larga ozi qidirgan anime sini topip berish va korish.
Sizni maqsatingiz admin larga yordam berish siz faqat admin lar bilan gaplaship yordam berasiz adminni etkanini bajarish shart.
Siz Admin panelidagi HAR BIR funksiyani, eng mayda detallarigacha boshqara olasiz.
Quyidagi JSON formatidagi buyruqlarni vaziyatga qarab qaytaring.
Va yana san admin lar ga json ni jonat mang siz json ni bot ga buyruq sfati da jonatin agar admin siz ga buyruq bersa uni json sfati da yozip bot ga buyurq qilip jonat admin ga jonat mang 

--- 1. ANIME VA KODLARNI CHUKUR TAHRIRLASH ---
- Yangi anime qo'shish (Auto): {{"cmd": "start_add_anime", "title": "Nomi", "genre": "Janr"}}
- Anime o'chirish: {{"cmd": "delete_anime", "code": "147"}}
- Nomini o'zgartirish: {{"cmd": "edit_title", "code": "147", "new_title": "Yangi nom"}}
- QISM QO'SHISH (Video): {{"cmd": "add_part_req", "code": "147"}}
- QISM O'CHIRISH (Specific): {{"cmd": "delete_part", "code": "147", "part_number": 5}}
- POSTER ALMASHTIRISH: {{"cmd": "change_poster_req", "code": "147"}}
- TUGMA (KNOPKA) MATNINI O'ZGARTIRISH: {{"cmd": "edit_button_text", "code": "147", "text": "Tomosha"}}
- TUGMA URL'INI O'ZGARTIRISH: {{"cmd": "edit_button_url", "code": "147", "url": "https://..."}}
- FORWARD STATUS: {{"cmd": "set_forward", "code": "147", "status": false}}
- JANRNI O'ZGARTIRISH: {{"cmd": "edit_genre", "code": "147", "new_genre": "Action"}}
- OVOZ BERGAN STUDIYANI O'ZGARTIRISH: {{"cmd": "edit_voice", "code": "147", "voice": "AniLibria"}}
- KOD STATISTIKASINI KO'RISH: {{"cmd": "code_stat", "code": "147"}}

--- 2. KANAL VA POSTLAR ---
- Kanalga post chiqarish: {{"cmd": "post_to_channel", "code": "147"}}
- Kechiktirib chiqarish: {{"cmd": "schedule_post", "code": "147", "delay_minutes": 60}}
- Kanal qo'shish (Majburiy): {{"cmd": "add_channel", "id": -100..., "link": "...", "type": "sub"}}
- Kanal qo'shish (Asosiy): {{"cmd": "add_channel", "id": -100..., "link": "...", "type": "main", "username": "kanal_user"}}
- Kanal o'chirish: {{"cmd": "del_channel", "id": -100..., "type": "sub"}}
- Kanallar ro'yxatini ko'rish: {{"cmd": "list_channels", "type": "sub"}}

--- 3. FOYDALANUVCHILAR VA MOLIYA (FULL) ---
- VIP berish: {{"cmd": "give_vip", "user_id": 123, "days": 30}}
- VIP olish: {{"cmd": "remove_vip", "user_id": 123}}
- Balansga pul qo'shish (+): {{"cmd": "balance_add", "user_id": 123, "amount": 50000}}
- Balansdan pul olish (-): {{"cmd": "balance_remove", "user_id": 123, "amount": 10000}}
- Ban qilish: {{"cmd": "ban_user", "user_id": 123, "reason": "..."}}
- Bandan olish: {{"cmd": "unban_user", "user_id": 123}}
- Banlanganlar ro'yxati: {{"cmd": "list_banned"}}
- User haqida to'liq info: {{"cmd": "user_info", "user_id": 123}}
- User qidirish (ID bo'yicha): {{"cmd": "check_user", "user_id": 123}}
- Ommaviy user qo'shish (matn orqali): {{"cmd": "mass_add_users", "ids": [123, 456, 789]}}

--- 4. TO'LOVLAR (PAYMENTS) ---
- Kutilayotgan to'lovlarni ko'rish: {{"cmd": "list_payments"}}
- To'lovni tasdiqlash: {{"cmd": "approve_payment", "request_id": 5, "amount": 15000}}
- To'lovni rad etish: {{"cmd": "reject_payment", "request_id": 5}}

--- 5. TIZIM VA ADMINLAR ---
- Admin qo'shish: {{"cmd": "add_admin", "user_id": 123}}
- Admin o'chirish: {{"cmd": "remove_admin", "user_id": 123}}
- Adminlar ro'yxati: {{"cmd": "list_admins"}}
- VIP narxlarni o'zgartirish: {{"cmd": "set_vip_price", "tariff": "1month", "price": 20000}}
- Karta raqamini o'zgartirish: {{"cmd": "set_card", "number": "8600..."}}
- Xabar tarqatish (Broadcast) - Hammasiga: {{"cmd": "broadcast", "target": "all", "text": "..."}}
- Xabar tarqatish - VIP larga: {{"cmd": "broadcast", "target": "vip", "text": "..."}}
- Xabar tarqatish - Oddiy larga: {{"cmd": "broadcast", "target": "regular", "text": "..."}}
- Shaxsiy xabar yuborish: {{"cmd": "send_private", "user_id": 123, "text": "..."}}
- Botni o'chirish/yoqish: {{"cmd": "bot_switch", "status": false}}
- Bot statistikasi: {{"cmd": "get_stats"}}

CONTEXT:
Jami userlar: {total_users}
Bugungi userlar: {today_users}
VIP userlar: {vip_users}
Kutilayotgan to'lovlar soni: {pending_count}
Bot holati: {"Active" if bot_status else "Inactive"}
Tarix: {context}
Admin buyrug'i: "{prompt_text}"

AGAR ADMIN BIROR NARSA SO'RASA, O'SHA ISHNI QILISH UCHUN ENG MOS JSON BUYRUQNI QAYTAR.
"""
        response = await ai_model.generate_content_async(system_prompt)
        result_text = response.text.strip()
        
        # JSON tozalash
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()

        # Tarixga yozish
        if message.from_user.id in ai_sessions:
            ai_sessions[message.from_user.id].append(f"AI: {result_text}")

        try:
            command = json.loads(result_text)
            cmd = command.get("cmd")

            # ==========================================
            # 1. ANIME VA KODLAR (Deep Editing)
            # ==========================================
            if cmd == "start_add_anime":
                title = command.get("title")
                genre = command.get("genre")
                poster_id = None
                media_type = 'photo'
                if message.photo: poster_id = message.photo[-1].file_id
                elif message.video: poster_id = message.video.file_id; media_type='video'
                elif message.document: poster_id = message.document.file_id; media_type='document'
                
                # Reply check
                if not poster_id and message.reply_to_message:
                    if message.reply_to_message.photo: poster_id = message.reply_to_message.photo[-1].file_id
                    elif message.reply_to_message.video: poster_id = message.reply_to_message.video.file_id; media_type='video'
                    if not title and message.reply_to_message.caption:
                         title = message.reply_to_message.caption.split('\n')[0][:50]

                if poster_id:
                     async with state.proxy() as data:
                        data['new_anime_title'] = title
                        data['new_anime_poster'] = poster_id
                        data['new_anime_media_type'] = media_type 
                        data['new_anime_genre'] = genre
                        data['new_anime_parts'] = []
                     await AIState.waiting_video.set()
                     await loading.edit_text(f"✅ <b>{title}</b> qabul qilindi.\nEndi qismlarni (video) yuboring.", parse_mode="HTML")
                else:
                     await loading.edit_text("❌ Iltimos, anime rasmi yoki videosini birga yuboring (yoki reply qiling).")

            elif cmd == "delete_anime":
                code = str(command.get("code"))
                if await delete_kino_code(code):
                    await loading.edit_text(f"🗑 Anime {code} butunlay o'chirildi.")
                else:
                    await loading.edit_text(f"❌ Kod {code} topilmadi.")

            elif cmd == "edit_title":
                code = str(command.get("code"))
                new_title = command.get("new_title")
                await update_anime_code(code, code, new_title)
                await loading.edit_text(f"✏️ Anime nomi o'zgardi:\n{new_title}")

            elif cmd == "edit_genre":
                code = str(command.get("code"))
                new_genre = command.get("new_genre")
                await update_anime_genre(code, new_genre)
                await loading.edit_text(f"🎭 Janr o'zgardi: {new_genre}")
                
            elif cmd == "edit_voice":
                code = str(command.get("code"))
                voice = command.get("voice")
                # Bu funksiyani database.py ga qo'shish kerak yoki update_anime_poster orqali qilish kerak
                # Hozircha oddiy xabar
                await loading.edit_text(f"⚠️ Bu funksiya database.py da to'liq integratsiya qilinmagan, lekin buyruq qabul qilindi: {voice}")

            elif cmd == "set_forward":
                code = str(command.get("code"))
                status = bool(command.get("status"))
                await set_anime_forward_status(code, status)
                res = "Ruxsat berildi ✅" if status else "Taqiqlandi ⛔️"
                await loading.edit_text(f"🔄 Forward statusi: {res}")
            
            elif cmd == "code_stat":
                code = str(command.get("code"))
                stat = await get_code_stat(code)
                if stat:
                     await loading.edit_text(f"📊 Kod: {code}\n👁 Viewed: {stat['viewed']}\n🔍 Searched: {stat['searched']}")
                else:
                     await loading.edit_text("❌ Statistika yo'q.")

            # --- QIYIN OPERATSIYALAR (Add/Del Part, Poster, Button) ---
            elif cmd == "delete_part":
                code = str(command.get("code"))
                part_num = int(command.get("part_number"))
                res = await delete_part_from_anime(code, part_num)
                if res:
                    await loading.edit_text(f"🗑 {code}-koddan {part_num}-qism o'chirildi.")
                else:
                    await loading.edit_text("❌ Xatolik. Qism topilmadi.")

            elif cmd == "add_part_req":
                code = str(command.get("code"))
                user_data[message.from_user.id] = {'action': 'add_part', 'code': code}
                await loading.edit_text(f"📥 {code} uchun video (qism) yuboring. Men uni qo'shib qo'yaman.")

            elif cmd == "change_poster_req":
                code = str(command.get("code"))
                user_data[message.from_user.id] = {'action': 'edit_post', 'step': 'new_poster', 'code': code}
                await loading.edit_text(f"🖼 {code} uchun yangi rasm/video yuboring.")

            elif cmd == "edit_button_text":
                code = str(command.get("code"))
                txt = command.get("text")
                kino = await get_kino_by_code(code)
                if kino:
                    await update_anime_poster(code, kino['poster_file_id'], kino['caption'], kino['media_type'], txt, kino['button_url'])
                    await loading.edit_text(f"🔘 Tugma matni o'zgardi: {txt}")
                else:
                    await loading.edit_text("❌ Kod topilmadi.")
            
            elif cmd == "edit_button_url":
                code = str(command.get("code"))
                url = command.get("url")
                kino = await get_kino_by_code(code)
                if kino:
                    await update_anime_poster(code, kino['poster_file_id'], kino['caption'], kino['media_type'], kino['button_text'], url)
                    await loading.edit_text(f"🔗 Tugma URL'i o'zgardi: {url}")
                else:
                    await loading.edit_text("❌ Kod topilmadi.")

            # ==========================================
            # 2. FOYDALANUVCHILAR VA MOLIYA (FULL)
            # ==========================================
            elif cmd == "user_info":
                uid = int(command.get("user_id"))
                profile = await get_user_profile(uid)
                is_banned = await is_user_banned(uid)
                txt = f"👤 <b>INFO:</b> {uid}\n💰 Balans: {profile['balance']}\n💎 VIP: {profile['is_vip']}\n🚫 Ban: {is_banned}"
                await loading.edit_text(txt, parse_mode="HTML")

            elif cmd == "give_vip":
                 uid = int(command.get("user_id"))
                 days = int(command.get("days"))
                 await give_vip(uid, days)
                 await loading.edit_text(f"💎 {uid} ga {days} kun VIP berildi.")

            elif cmd == "remove_vip":
                uid = int(command.get("user_id"))
                await remove_vip(uid)
                await loading.edit_text(f"❌ {uid} dan VIP olindi.")

            elif cmd == "balance_add":
                uid = int(command.get("user_id"))
                amt = int(command.get("amount"))
                await update_user_balance(uid, amt)
                await loading.edit_text(f"💰 {uid} balansiga +{amt} qo'shildi.")
            
            elif cmd == "balance_remove":
                uid = int(command.get("user_id"))
                amt = int(command.get("amount"))
                await update_user_balance(uid, -amt)
                await loading.edit_text(f"💸 {uid} balansidan -{amt} olindi.")

            elif cmd == "ban_user":
                uid = int(command.get("user_id"))
                reason = command.get("reason", "Admin")
                if uid in ADMINS:
                    await loading.edit_text("❌ Adminni ban qilib bo'lmaydi.")
                else:
                    await ban_user(uid, reason)
                    await loading.edit_text(f"🚫 User {uid} ban qilindi.")

            elif cmd == "unban_user":
                uid = int(command.get("user_id"))
                await unban_user(uid)
                await loading.edit_text(f"✅ User {uid} bandan olindi.")
            
            elif cmd == "list_banned":
                banned = await get_all_banned_users()
                if not banned:
                    await loading.edit_text("✅ Banlanganlar yo'q.")
                else:
                    txt = "🚫 <b>Banlanganlar:</b>\n" + "\n".join([f"{u['user_id']} ({u['reason']})" for u in banned])
                    await loading.edit_text(txt, parse_mode="HTML")
            
            elif cmd == "mass_add_users":
                ids = command.get("ids", [])
                if ids:
                    await add_multiple_users(ids)
                    await loading.edit_text(f"✅ {len(ids)} ta user bazaga qo'shildi.")
                else:
                    await loading.edit_text("❌ ID lar topilmadi.")

            # --- TO'LOV TIZIMI (Payment) ---
            elif cmd == "list_payments":
                reqs = await get_pending_payment_requests()
                if not reqs:
                    await loading.edit_text("📭 To'lov so'rovlari yo'q.")
                else:
                    txt = "💳 <b>Kutilayotgan to'lovlar:</b>\n\n"
                    for r in reqs:
                        txt += f"🆔 ID: {r['id']} | 👤 User: {r['user_id']}\n"
                    txt += "\nTasdiqlash uchun: 'ID 5 ni 15000 ga tasdiqla' deng."
                    await loading.edit_text(txt, parse_mode="HTML")

            elif cmd == "approve_payment":
                rid = int(command.get("request_id"))
                amt = int(command.get("amount"))
                uid = await approve_payment_request(rid, amt)
                if uid:
                    await loading.edit_text(f"✅ To'lov (ID: {rid}) tasdiqlandi. {uid} ga {amt} so'm tushdi.")
                else:
                    await loading.edit_text("❌ Bunday ID li so'rov topilmadi.")

            elif cmd == "reject_payment":
                rid = int(command.get("request_id"))
                await reject_payment_request(rid)
                await loading.edit_text(f"❌ To'lov (ID: {rid}) rad etildi.")

            # ==========================================
            # 3. KANAL VA TIZIM SOZLAMALARI
            # ==========================================
            elif cmd == "post_to_channel":
                code = str(command.get("code"))
                kino = await get_kino_by_code(code)
                if kino:
                    for ch in MAIN_CHANNELS:
                         try: await send_channel_post(ch, kino, code)
                         except: pass
                    await loading.edit_text(f"📤 Post kanallarga chiqdi (Kod: {code}).")
                else:
                    await loading.edit_text("❌ Kod topilmadi.")

            elif cmd == "schedule_post":
                code = str(command.get("code"))
                delay = int(command.get("delay_minutes"))
                asyncio.create_task(delayed_post_task(message.chat.id, code, delay*60))
                await loading.edit_text(f"⏰ Post {delay} daqiqadan keyin chiqadi.")

            elif cmd == "add_channel":
                cid = int(command.get("id"))
                link = command.get("link")
                ctype = command.get("type")
                username = command.get("username", "")
                await add_channel_to_db(cid, link, ctype, username)
                await load_channels()
                await loading.edit_text(f"📡 Kanal qo'shildi: {cid} ({ctype})")

            elif cmd == "del_channel":
                cid = int(command.get("id"))
                ctype = command.get("type")
                await delete_channel_from_db(cid, ctype)
                await load_channels()
                await loading.edit_text(f"🗑 Kanal o'chirildi: {cid}")

            elif cmd == "list_channels":
                ctype = command.get("type")
                await load_channels()
                chs = CHANNELS if ctype == 'sub' else MAIN_CHANNELS
                txt = f"📋 <b>{ctype.upper()} kanallar:</b>\n" + "\n".join([str(x) for x in chs])
                await loading.edit_text(txt, parse_mode="HTML")

            elif cmd == "set_vip_price":
                tariff = command.get("tariff")
                price = int(command.get("price"))
                await update_vip_price(tariff, price)
                await loading.edit_text(f"💰 {tariff} narxi {price} bo'ldi.")

            elif cmd == "set_card":
                num = command.get("number")
                await set_card_number(num)
                await loading.edit_text(f"💳 Karta o'zgardi: {num}")

            elif cmd == "broadcast":
                target = command.get("target")
                text = command.get("text")
                users = []
                if target == "all": users = await get_all_user_ids()
                elif target == "vip": users = await get_all_vip_user_ids()
                elif target == "regular": users = await get_all_regular_user_ids()
                asyncio.create_task(broadcast_message(message, users, text, target))
                await loading.edit_text(f"🚀 Xabar {target} auditoriyaga ketmoqda.")
            
            elif cmd == "send_private":
                uid = int(command.get("user_id"))
                text = command.get("text")
                try:
                    await bot.send_message(uid, f"🔔 <b>Admindan:</b>\n{text}", parse_mode="HTML")
                    await loading.edit_text(f"✅ Xabar yuborildi: {uid}")
                except:
                    await loading.edit_text("❌ Yuborilmadi (bloklagan bo'lishi mumkin).")

            elif cmd == "bot_switch":
                status = bool(command.get("status"))
                await set_bot_active(status)
                await loading.edit_text(f"🤖 Bot holati: {status}")
            
            elif cmd == "get_stats":
                msg = (
                    f"📊 <b>STATISTIKA</b>\n"
                    f"👥 Jami userlar: {total_users}\n"
                    f"📅 Bugungi userlar: {today_users}\n"
                    f"💎 VIP userlar: {vip_users}\n"
                    f"💳 To'lovlar: {pending_count}"
                )
                await loading.edit_text(msg, parse_mode="HTML")

            elif cmd == "add_admin":
                uid = int(command.get("user_id"))
                await add_admin(uid)
                ADMINS.add(uid)
                await loading.edit_text(f"👮‍♂️ Admin qo'shildi: {uid}")
            
            elif cmd == "remove_admin":
                uid = int(command.get("user_id"))
                if uid in START_ADMINS:
                    await loading.edit_text("❌ Asosiy adminni o'chirish mumkin emas.")
                else:
                    await remove_admin(uid)
                    ADMINS.discard(uid)
                    await loading.edit_text(f"🗑 Admin o'chirildi: {uid}")
            
            elif cmd == "list_admins":
                admins = await get_all_admins()
                txt = "👮‍♂️ <b>Adminlar:</b>\n" + "\n".join([str(a) for a in admins])
                await loading.edit_text(txt, parse_mode="HTML")

            # --- AGAR BUYRUQ TUSHUNARSIZ BOLSA ---
            else:
                # Chatlashish rejimi
                reply = command.get("text", result_text)
                await loading.edit_text(reply)

        except json.JSONDecodeError:
            await loading.edit_text(result_text)

    except Exception as e:
        await loading.edit_text(f"❌ Xatolik (Ultimate Mode): {e}")

# --- VIDEO YIG'ISH HANDLERI ---

# --- VIDEO YIG'ISH HANDLERI ---
@dp.message_handler(state=AIState.waiting_video, content_types=['video', 'document', 'text'])
async def collect_anime_videos(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() in ['boldi', 'tamom', 'stop', '/done']:
        async with state.proxy() as data:
            title = data.get('new_anime_title')
            poster = data.get('new_anime_poster')
            media_type = data.get('new_anime_media_type', 'photo')
            parts = data.get('new_anime_parts')
            # AI aniqlagan janrni olamiz. Agar yo'q bo'lsa "Anime" deb yozamiz.
            genre = data.get('new_anime_genre', 'Anime') 
        
        new_code = str(random.randint(1000, 9999))
        
        # BAZAGA SAQLASH (genre parametrini qosdik)
        await add_anime(new_code, title, poster, parts, media_type=media_type, genre=genre) 
        
        await state.finish()
        await AIState.chat_mode.set()
        await message.answer(
            f"✅ <b>{title}</b> saqlandi!\n"
            f"🔢 Kod: <code>{new_code}</code>\n"
            f"🎭 Janr: {genre}", 
            parse_mode="HTML"
        )
        return

    # Videoni yig'ish (eski kod)
    file_id = None
    if message.video: file_id = message.video.file_id
    elif message.document: file_id = message.document.file_id
    
    if file_id:
        async with state.proxy() as data:
            data['new_anime_parts'].append(file_id)
        await message.answer(f"📥 {len(data['new_anime_parts'])}-qism.")
    else:
        await message.answer("🎥 Video tashlang yoki 'Boldi' deng.")

# --- BACKGROUND TASK ---
async def delayed_post_task(admin_chat_id, code, delay_seconds):
    await asyncio.sleep(delay_seconds)
    kino = await get_kino_by_code(code)
    if kino and MAIN_CHANNELS:
        count = 0
        for ch_id in MAIN_CHANNELS:
            try:
                await send_channel_post(ch_id, kino, code)
                count += 1
            except: pass
        try: await bot.send_message(admin_chat_id, f"⏰ Post chiqdi: {kino['title']}")
        except: pass

# --- AI HANDLER MAX TUGADI ---

# --- (MEN QOSDIM) AI HANDLER TUGADI ---
 # --- AI RUXSAT TIZIMI (HUMAN-IN-THE-LOOP) ---
 # --- AI RUXSAT TIZIMI (ADMIN TASDIQLASH REJIMI) ---
async def ask_ai_permission(action_type, description, execute_data):
    """
    AI adminlardan ruxsat so'raydi.
    action_type: 'fix_genre', 'del_channel' va h.k.
    description: Adminga tushuntirish matni.
    execute_data: Agar ruxsat berilsa, bajariladigan ma'lumot (dict).
    """
    # 1. Har bir so'rovga unikal ID beramiz
    request_id = str(uuid.uuid4())[:8]
    
    # 2. Xotiraga saqlaymiz
    ai_pending_actions[request_id] = {
        'type': action_type,
        'data': execute_data,
        'desc': description
    }

    # 3. Tugmalarni yasaymiz
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ruxsat berish", callback_data=f"ai_approve:{request_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"ai_deny:{request_id}")
    )

    # 4. Asosiy adminga (yoki barchasiga) yuboramiz
    for admin_id in START_ADMINS: # Faqat bosh adminlarga
        try:
            await bot.send_message(
                admin_id,
                f"🤖 <b>AI RUXSAT SO'RAMOQDA</b>\n\n"
                f"📝 <b>Harakat:</b> {action_type}\n"
                f"ℹ️ <b>Sabab:</b> {description}\n\n"
                f"O'zgartirish kiritaymi?",
                reply_markup=kb,
                parse_mode="HTML"
            )
        except: pass

@dp.callback_query_handler(lambda c: c.data.startswith("ai_approve:") or c.data.startswith("ai_deny:"))
async def process_ai_decision(call: types.CallbackQuery):
    action, req_id = call.data.split(":")
    
    # Agar xotirada bu so'rov yo'q bo'lsa (bot o'chib yongan bo'lsa)
    if req_id not in ai_pending_actions:
        await call.answer("❌ Bu so'rov eskirgan yoki topilmadi.", show_alert=True)
        await call.message.delete()
        return

    req = ai_pending_actions[req_id]
    
    if action == "ai_deny":
        # RAD ETILDI
        del ai_pending_actions[req_id]
        await call.message.edit_text(f"❌ <b>RAD ETILDI</b>\n\n{req['desc']}", parse_mode="HTML")
        await call.answer("Xop, o'zgartirmayman.")
    
    elif action == "ai_approve":
        # RUXSAT BERILDI - ISHNI BAJARAMIZ
        task_type = req['type']
        data = req['data']
        
        try:
            if task_type == 'fix_genre':
                # Bazada janrni o'zgartirish
                await update_anime_genre(data['code'], data['new_genre'])
                res_text = f"✅ Janr o'zgartirildi: {data['new_genre']}"
                
            elif task_type == 'del_channel':
                # Kanalni o'chirish
                await delete_channel_from_db(data['channel_id'], data['channel_type'])
                res_text = f"✅ Kanal bazadan o'chirildi: {data['channel_id']}"
            
            # ... boshqa turlar bo'lsa shu yerga qo'shiladi ...

            # Logga yozamiz
            await log_ai_action(task_type, f"Admin ruxsati bilan: {req['desc']}")
            
            # Xabarni yangilaymiz
            await call.message.edit_text(f"✅ <b>BAJARILDI</b>\n\n{req['desc']}\n\n{res_text}", parse_mode="HTML")
            
            # Xotiradan o'chiramiz
            del ai_pending_actions[req_id]
            
        except Exception as e:
            await call.message.edit_text(f"❌ Xatolik yuz berdi: {e}")

    await call.answer()


# --- ЖАҢА КӨМЕКШІ ФУНКЦИЯ (BROADCAST TYPE MENU) ---
async def show_broadcast_type_menu(user_id, target_type):
    """
    Рассылка түрін таңдау мәзірі (Мәтін немесе Пост ID)
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("✍️ Matn yozish"), KeyboardButton("🔄 Post (ID orqali)"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    
    user_data[user_id] = {
        'action': 'broadcast_choose_mode',
        'target_group': target_type # 'all', 'vip', 'regular'
    }
    
    await bot.send_message(
        user_id, 
        f"📢 <b>{target_type.upper()}</b> foydalanuvchilarga xabar yuborish.\n\n"
        "Qaysi usulda yuborasiz?", 
        reply_markup=kb, 
        parse_mode="HTML"
    )

# --- HANDLE ALL MESSAGES (TOЛЫҚ ЖАҢАРТЫЛҒАН) ---
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    action = data.get('action')

    # 1. ТӨЛЕМ (PAYMENT)
    if action == 'payment_upload':
        if message.photo:
            photo_file_id = message.photo[-1].file_id
            await add_payment_request(user_id, photo_file_id)
            user_data.pop(user_id, None)

            for admin_id in ADMINS:
                try:
                    await bot.send_photo(
                        admin_id,
                        photo_file_id,
                        caption=f"💵 YANGI TO'LOV!\n\n👤 User: @{message.from_user.username or 'no_username'} (ID: {user_id})\n📸 Chek yuborildi\n\nTasdiqlash uchun: 💳 To'lov so'rovlari"
                    )
                except:
                    pass

            is_admin = user_id in ADMINS
            await message.answer("✅ To'lov cheki yuborildi! Admin tasdiqlashi bilan balansingizga qo'shiladi.", reply_markup=user_panel_keyboard(is_admin=is_admin))
        else:
            await message.answer("❌ Iltimos, to'lov cheki rasmini yuboring!")

    # 2. BUYURTMA (ORDER)
    elif action == 'order_service':
        user_data.pop(user_id, None)
        for admin_id in ADMINS:
            try:
                await bot.send_message(
                    admin_id,
                    f"📦 YANGI BUYURTMA!\n\n👤 User: @{message.from_user.username or 'no_username'} (ID: {user_id})\n💬 Xabar:\n{message.text}"
                )
            except:
                pass
        is_admin = user_id in ADMINS
        await message.answer("✅ Buyurtmangiz yuborildi! Admin siz bilan tez orada bog'lanadi.", reply_markup=user_panel_keyboard(is_admin=is_admin))

    # 3. ADMINMEN BAILANYS (CONTACT)
    elif action == 'contact_admin':
        user_data.pop(user_id, None)
        
        is_vip = False
        try:
            is_vip = await is_user_vip(user_id)
        except:
            is_vip = False
            
        status_text = "💎 VIP USER" if is_vip else "👤 Foydalanuvchi"
        username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
        full_name = message.from_user.full_name
        
        msg_text = message.text if message.text else "(Rasm yoki media)"
        
        for admin_id in ADMINS:
            try:
                keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✉️ Javob yozish", callback_data=f"reply_user:{user_id}"))
                await bot.send_message(
                    admin_id,
                    f"📩 <b>Yangi xabar ({status_text}):</b>\n\n"
                    f"👤 <b>Ism:</b> {full_name}\n"
                    f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                    f"🔗 <b>Username:</b> {username}\n\n"
                    f"💬 <b>Xabar:</b>\n{msg_text}",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                if not message.text:
                    await message.send_copy(admin_id)
            except:
                pass

        is_admin_user = user_id in ADMINS
        await message.answer("✅ Xabaringiz yuborildi. Admin tez orada javob beradi.",
                           reply_markup=user_panel_keyboard(is_admin=is_admin_user, is_vip=is_vip))

    # 4. USERGE JAUAP (REPLY)
    elif action == 'reply_to_user':
        target = data.get('target_user')
        user_data.pop(user_id, None)
        
        admin_name = message.from_user.full_name
        admin_id_show = message.from_user.id
        
        try:
            await bot.send_message(
                target, 
                f"📨 <b>Admindan javob:</b>\n\n"
                f"👮‍♂️ <b>Admin:</b> {admin_name} (ID: {admin_id_show})\n\n"
                f"💬 <b>Javob:</b>\n{message.text}",
                parse_mode="HTML"
            )
            await message.answer("✅ Javob foydalanuvchiga yuborildi.", reply_markup=admin_panel_keyboard())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=admin_panel_keyboard())

    # --- ADMIN ACTIONS ---
    
    elif action == 'admin_give_vip':
        step = data.get('step')
        if step == 'user_id':
            try:
                vip_user_id = int(message.text.strip())
                user_data[user_id]['vip_user_id'] = vip_user_id
                user_data[user_id]['step'] = 'days'
                await message.answer("⏱ Necha kun VIP bermoqchisiz?", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri ID format!")
        elif step == 'days':
            try:
                days = int(message.text.strip())
                vip_user_id = data['vip_user_id']
                await give_vip(vip_user_id, days)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Muvaffaqiyatli!\n\n👤 User ID: {vip_user_id}\n💎 VIP berildi: {days} kun", reply_markup=admin_panel_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format!")

    elif action == 'admin_remove_vip':
        try:
            vip_user_id = int(message.text.strip())
            await remove_vip(vip_user_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ VIP muvaffaqiyatli olindi!\n\n👤 User ID: {vip_user_id}", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'update_card':
        card_number = message.text.strip()
        await set_card_number(card_number)
        user_data.pop(user_id, None)
        await message.answer(f"✅ Yangi karta saqlandi: {card_number}", reply_markup=admin_panel_keyboard())

    elif action == 'admin_add_balance':
        step = data.get('step')
        if step == 'user_id':
            try:
                balance_user_id = int(message.text.strip())
                user_data[user_id]['balance_user_id'] = balance_user_id
                user_data[user_id]['step'] = 'amount'
                await message.answer("💰 Qancha pul qo'shasiz? (so'mda)", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri ID format!")
        elif step == 'amount':
            try:
                amount = int(message.text.strip())
                balance_user_id = data['balance_user_id']
                await update_user_balance(balance_user_id, amount)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Muvaffaqiyatli!\n\n👤 User ID: {balance_user_id}\n💰 Qo'shildi: {amount:,} so'm", reply_markup=admin_panel_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format!")

    elif action == 'admin_remove_balance':
        step = data.get('step')
        if step == 'user_id':
            try:
                balance_user_id = int(message.text.strip())
                user_data[user_id]['balance_user_id'] = balance_user_id
                user_data[user_id]['step'] = 'amount'
                await message.answer("💰 Qancha pul olasiz? (so'mda)", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri ID format!")
        elif step == 'amount':
            try:
                amount = int(message.text.strip())
                balance_user_id = data['balance_user_id']
                await update_user_balance(balance_user_id, -amount)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Muvaffaqiyatli!\n\n👤 User ID: {balance_user_id}\n💸 Olindi: {amount:,} so'm", reply_markup=admin_panel_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format!")

    elif action == 'approve_payment_amount':
        try:
            amount = int(message.text.strip())
            request_id = data['request_id']
            target_user = data['user_id']

            approved_user = await approve_payment_request(request_id, amount)
            user_data.pop(user_id, None)

            if approved_user:
                try:
                    await bot.send_message(
                        target_user,
                        f"✅ To'lovingiz tasdiqlandi!\n\n💰 Balansingizga {amount:,} so'm qo'shildi!"
                    )
                except:
                    pass

                await message.answer(
                    f"✅ To'lov tasdiqlandi!\n\n👤 User ID: {target_user}\n💰 Qo'shildi: {amount:,} so'm",
                    reply_markup=admin_panel_keyboard()
                )
            else:
                await message.answer("❌ Xatolik yuz berdi!", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri format! Raqam kiriting.")

    elif action == 'update_vip_price':
        try:
            price = int(message.text.strip())
            tariff = data['tariff']
            await update_vip_price(tariff, price)
            user_data.pop(user_id, None)
            tariff_names = {'1month': '1 oylik', '3month': '3 oylik', '6month': '6 oylik'}
            await message.answer(f"✅ Yangi narx saqlandi!\n\n{tariff_names.get(tariff, tariff)} - {price:,} so'm", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri format! Raqam kiriting.")

    elif action == 'add_channel':
        step = data.get('step')
        ctype = data.get('channel_type')

        if step == 'id':
            try:
                channel_id = int(message.text.strip())
                user_data[user_id]['channel_id'] = channel_id
                user_data[user_id]['step'] = 'link'
                await message.answer("🔗 Endi kanal HTTPS linkini yuboring (masalan: https://t.me/kanalingiz):", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format. Raqam kiriting!")

        elif step == 'link':
            channel_link = message.text.strip()
            if not channel_link.startswith('http'):
                await message.answer("❌ Iltimos HTTPS link yuboring! (https://t.me/...)")
                return

            user_data[user_id]['channel_link'] = channel_link
            channel_id = data.get('channel_id')

            if ctype == 'main':
                user_data[user_id]['step'] = 'username'
                await message.answer("👤 Endi kanal username kiriting (@kanal yoki kanal):", reply_markup=admin_back_keyboard())
            else:
                try:
                    member = await bot.get_chat_member(channel_id, message.from_user.id)
                    if member.status not in ['administrator', 'creator']:
                        await message.answer("❌ Siz bu kanalda admin emassiz! Kanal qo'shish uchun admin bo'lishingiz kerak.")
                        user_data.pop(user_id, None)
                        return

                    await add_channel_to_db(channel_id, channel_link, ctype, "") 
                    await load_channels()
                    user_data.pop(user_id, None)
                    await message.answer(f"✅ Majburiy obuna kanali muvaffaqiyatli qo'shildi!", reply_markup=admin_panel_keyboard())
                except Exception as e:
                    await message.answer(f"❌ Xatolik: {e}\n\nKanal ID to'g'ri va siz admin ekanligingizni tekshiring!")
                    user_data.pop(user_id, None)

        elif step == 'username':
            if ctype != 'main':
                user_data.pop(user_id, None)
                return

            username = message.text.strip().replace('@', '')
            channel_id = data.get('channel_id')
            channel_link = data.get('channel_link')

            try:
                member = await bot.get_chat_member(channel_id, message.from_user.id)
                if member.status not in ['administrator', 'creator']:
                    await message.answer("❌ Siz bu kanalda admin emassiz! Kanal qo'shish uchun admin bo'lishingiz kerak.")
                    user_data.pop(user_id, None)
                    return

                await add_channel_to_db(channel_id, channel_link, ctype, username)
                await load_channels()
                user_data.pop(user_id, None)
                await message.answer(f"✅ Asosiy kanal muvaffaqiyatli qo'shildi!\n📌 Username: @{username}", reply_markup=admin_panel_keyboard())
            except Exception as e:
                await message.answer(f"❌ Xatolik: {e}\n\nKanal ID to'g'ri va siz admin ekanligingizni tekshiring!")
                user_data.pop(user_id, None)

    elif action == 'delete_code':
        code = message.text.strip()
        if await delete_kino_code(code):
            user_data.pop(user_id, None)
            await message.answer(f"✅ Kod {code} o'chirildi!", reply_markup=admin_panel_keyboard())
        else:
            await message.answer("❌ Kod topilmadi yoki o'chirishda xatolik.")

    # --- ANIME YUKLASH (TUZATILGAN: Fasl sұрамайды, 1-qism format) ---
    elif action == 'add_anime':
        step = data.get('step')

        if step == 'code':
            user_data[user_id]['code'] = message.text.strip()
            user_data[user_id]['step'] = 'title'
            await message.answer("📝 Anime nomini kiriting:", reply_markup=admin_back_keyboard())

        elif step == 'title':
            user_data[user_id]['title'] = message.text.strip()
            # ТҮЗЕТУ: 'fasl' сұрамаймыз, бірден 'genre' сұраймыз
            user_data[user_id]['step'] = 'genre'
            await message.answer("🎭 Anime janrini kiriting (masalan: Action, Comedy):", reply_markup=admin_back_keyboard())

        elif step == 'genre':
            user_data[user_id]['genre'] = message.text.strip()
            user_data[user_id]['step'] = 'ovoz_berdi'
            await message.answer("🎙 Ovoz bergan studiya/jamoa nomini kiriting (masalan: 'AniLibria')\n\nE'tiborsiz qoldirish uchun /skip yuboring:", reply_markup=admin_back_keyboard())

        elif step == 'ovoz_berdi':
            if message.text == '/skip':
                user_data[user_id]['ovoz_berdi'] = ""
            elif message.text:
                user_data[user_id]['ovoz_berdi'] = message.text.strip()
            else:
                await message.answer("❌ Studiya nomini matn qilib yozing!")
                return
                
            user_data[user_id]['step'] = 'poster'
            await message.answer("🖼 Poster (rasm yoki video) yuboring:", reply_markup=admin_back_keyboard())

        elif step == 'poster':
            if message.photo:
                user_data[user_id]['poster_file_id'] = message.photo[-1].file_id
                user_data[user_id]['media_type'] = 'photo'
            elif message.video:
                user_data[user_id]['poster_file_id'] = message.video.file_id
                user_data[user_id]['media_type'] = 'video'
            elif message.document:
                user_data[user_id]['poster_file_id'] = message.document.file_id
                user_data[user_id]['media_type'] = 'document'
            else:
                await message.answer("❌ Iltimos rasm, video yoki fayl yuboring!")
                return

            user_data[user_id]['step'] = 'parts'
            user_data[user_id]['parts'] = []
            await message.answer("📂 1-qismni (video/fayl) yuboring:", reply_markup=admin_back_keyboard())

        elif step == 'parts':
            if message.text == '/done':
                code = data['code']
                title = data['title']
                poster_file_id = data['poster_file_id']
                parts = data.get('parts', [])
                media_type = data.get('media_type', 'photo')
                genre = data.get('genre', 'Anime')
                ovoz_berdi = data.get('ovoz_berdi', '')
                
                channel_username = ""
                if MAIN_USERNAMES and MAIN_USERNAMES[0]:
                    channel_username = MAIN_USERNAMES[0]

                await add_anime(code, title, poster_file_id, parts, "", media_type, genre, True, channel_username, ovoz_berdi)
                
                user_data.pop(user_id, None)
                await message.answer(f"✅ Anime muvaffaqiyatli qo'shildi!\n📺 {title}\n📦 {len(parts)} qisim.", reply_markup=admin_panel_keyboard())
            else:
                # ТҮЗЕТУ: Видео қабылдағанда count шығару
                if message.video:
                    user_data[user_id]['parts'].append(message.video.file_id)
                    count = len(user_data[user_id]['parts'])
                    await message.answer(f"✅ {count}-qism qo'shildi.\nKeyingisini yuboring yoki tugatish uchun /done bosing.")
                elif message.document:
                    user_data[user_id]['parts'].append(message.document.file_id)
                    count = len(user_data[user_id]['parts'])
                    await message.answer(f"✅ {count}-qism qo'shildi.\nKeyingisini yuboring yoki tugatish uchun /done bosing.")
                else:
                    await message.answer("❌ Iltimos video yoki fayl yuboring! Yoki /done bosing.")

    elif action == 'edit_code_select':
        code = message.text.strip()
        kino = await get_kino_by_code(code)
        if not kino:
            await message.answer("❌ Kod topilmadi.")
            return

        user_data[user_id] = {'action': 'edit_code_menu', 'code': code}
        await message.answer(
            f"📝 Kod: {code}\n📺 Nomi: {kino['title']}\n\n"
            "Qaysi amalni bajarmoqchisiz?",
            reply_markup=edit_code_menu_keyboard()
        )

    elif action == 'edit_code_name':
        step = data.get('step')
        code = data.get('code')

        if step == 'new_code':
            user_data[user_id]['new_code'] = message.text.strip()
            user_data[user_id]['step'] = 'new_title'
            await message.answer("📝 Yangi nomini kiriting:", reply_markup=admin_back_keyboard())

        elif step == 'new_title':
            new_code = data['new_code']
            new_title = message.text.strip()
            await update_anime_code(code, new_code, new_title)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Kod va nom muvaffaqiyatli o'zgartirildi!\n\n📝 Yangi kod: {new_code}\n📺 Yangi nom: {new_title}", reply_markup=admin_panel_keyboard())

    elif action == 'add_part':
        code = data.get('code')
        if message.video:
            file_id = message.video.file_id
        elif message.document:
            file_id = message.document.file_id
        else:
            await message.answer("❌ Iltimos video yoki fayl yuboring!")
            return

        await add_part_to_anime(code, file_id)
        user_data.pop(user_id, None)
        await message.answer("✅ Qism muvaffaqiyatli qo'shildi!", reply_markup=admin_panel_keyboard())

    elif action == 'delete_part':
        code = data.get('code')
        try:
            part_number = int(message.text.strip())
            success = await delete_part_from_anime(code, part_number)
            user_data.pop(user_id, None)
            if success:
                await message.answer(f"✅ {part_number}-qism o'chirildi!", reply_markup=admin_panel_keyboard())
            else:
                await message.answer("❌ Noto'g'ri qism raqami.", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Iltimos raqam kiriting!", reply_markup=admin_panel_keyboard())

    elif action == 'edit_post':
        step = data.get('step')

        if step == 'code':
            code = message.text.strip()
            kino = await get_kino_by_code(code)
            if not kino:
                await message.answer("❌ Kod topilmadi.")
                return

            user_data[user_id]['code'] = code
            user_data[user_id]['step'] = 'new_poster'
            await message.answer("🖼 Yangi poster (rasm yoki video) yuboring yoki /skip:", reply_markup=admin_back_keyboard())

        elif step == 'new_poster':
            if message.text == '/skip':
                user_data[user_id]['new_poster'] = None
                user_data[user_id]['new_media_type'] = None
            else:
                if message.photo:
                    user_data[user_id]['new_poster'] = message.photo[-1].file_id
                    user_data[user_id]['new_media_type'] = 'photo'
                elif message.video:
                    user_data[user_id]['new_poster'] = message.video.file_id
                    user_data[user_id]['new_media_type'] = 'video'
                elif message.document:
                    user_data[user_id]['new_poster'] = message.document.file_id
                    user_data[user_id]['new_media_type'] = 'document'
                else:
                    await message.answer("❌ Iltimos rasm, video yoki fayl yuboring!")
                    return

            user_data[user_id]['step'] = 'button_text'
            await message.answer("🔘 Tugma matni yuboring (masalan: 'Tomosha qilish') yoki /skip:", reply_markup=admin_back_keyboard())

        elif step == 'button_text':
            if message.text == '/skip':
                code = data['code']
                kino = await get_kino_by_code(code)
                poster = data.get('new_poster') or kino['poster_file_id']
                media_type = data.get('new_media_type') or kino['media_type']

                await update_anime_poster(code, poster, "", media_type, None, None)
                user_data.pop(user_id, None)
                await message.answer("✅ Post muvaffaqiyatli tahrirlandi!", reply_markup=admin_panel_keyboard())
            else:
                button_text = message.text.strip()
                code = data['code']
                kino = await get_kino_by_code(code)

                poster = data.get('new_poster') or kino['poster_file_id']
                media_type = data.get('new_media_type') or kino['media_type']
                button_url = f"https://t.me/{BOT_USERNAME}?start={code}"

                await update_anime_poster(code, poster, "", media_type, button_text, button_url)
                user_data.pop(user_id, None)
                await message.answer("✅ Post va tugma muvaffaqiyatli tahrirlandi!", reply_markup=admin_panel_keyboard())

    elif action == 'view_stat':
        code = message.text.strip()
        stat = await get_code_stat(code)
        if stat:
            user_data.pop(user_id, None)
            await message.answer(
                f"📈 Kod {code} statistikasi:\n\n"
                f"🔍 Qidirildi: {stat['searched']} marta\n"
                f"👀 Ko'rildi: {stat['viewed']} marta",
                reply_markup=admin_panel_keyboard()
            )
        else:
            await message.answer("❌ Bu kod uchun statistika topilmadi.")

    elif action == 'add_admin':
        try:
            admin_id = int(message.text.strip())
            await add_admin(admin_id)
            ADMINS.add(admin_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Admin qo'shildi: {admin_id}", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'remove_admin':
        try:
            admin_id = int(message.text.strip())
            if admin_id in START_ADMINS:
                await message.answer("❌ Asosiy adminlarni o'chirib bo'lmaydi!")
                return
            await remove_admin(admin_id)
            ADMINS.discard(admin_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Admin o'chirildi: {admin_id}", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'broadcast_single_id':
        try:
            target_id = int(message.text.strip())
            user_data[user_id] = {'action': 'broadcast_single_message', 'target_id': target_id}
            await message.answer(f"📝 {target_id} ga yuboriladigan xabarni yozing:", reply_markup=admin_back_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'broadcast_single_message':
        target_id = data.get('target_id')
        user_data.pop(user_id, None)
        try:
            await bot.send_message(target_id, f"📢 <b>Xabar:</b>\n\n{message.text}", parse_mode="HTML")
            await message.answer(f"✅ Xabar {target_id} ga yuborildi.", reply_markup=admin_panel_keyboard())
        except Exception as e:
            await message.answer(f"❌ Xabar yuborilmadi: {e}", reply_markup=admin_panel_keyboard())

    # --- BROADCAST (Сен сұраған дұрыс логика) ---
    
    # 1. ТАҢДАУ
    elif action == 'broadcast_choose_mode':
        target = data.get('target_group') 
        
        if message.text == "✍️ Matn yozish":
            user_data[user_id] = {'action': 'broadcast_text_input', 'target_group': target}
            await message.answer(f"📝 {target.upper()} guruhiga xabarni yozing:", reply_markup=admin_back_keyboard())
            
        elif message.text == "🔄 Post (ID orqali)":
            user_data[user_id] = {'action': 'broadcast_post_input', 'target_group': target}
            await message.answer(
                "🔢 Kanal ID va Post ID ni quyidagi formatda yuboring:\n"
                "<code>-100123456789:45</code>\n\n"
                "Bu yerda: \n"
                "-100... - Kanal ID\n"
                "45 - Post ID",
                parse_mode="HTML",
                reply_markup=admin_back_keyboard()
            )
        else:
            await message.answer("❌ Iltimos, tugmalardan birini tanlang.")

    # 2. МӘТІН РЕТІНДЕ ТАРАТУ
    elif action == 'broadcast_text_input':
        target = data.get('target_group')
        user_data.pop(user_id, None)
        
        if target == 'all': users = await get_all_user_ids()
        elif target == 'vip': users = await get_all_vip_user_ids()
        elif target == 'regular': users = await get_all_regular_user_ids()
        else: users = []
            
        broadcast_info = {
            'from_chat_id': user_id,     
            'message_id': message.message_id 
        }
            
        # Бұл жерде біз алдыңғы хабарламада жазған дұрыс "background_broadcast" функциясын шақырамыз
        asyncio.create_task(background_broadcast(message, users, broadcast_info))

    # 3. POST FORWARD QILISH
    elif action == 'broadcast_post_input':
        inp = message.text.strip()
        target = data.get('target_group')
        
        try:
            if "/" in inp:
                parts = inp.split('/')
            elif ":" in inp:
                parts = inp.split(':')
            else:
                await message.answer("❌ Noto'g'ri format! '/' yoki ':' belgisi topilmadi.\nMasalan: @Anilordtv/1326")
                return

            post_id = int(parts[-1].strip())
            channel_identifier = parts[-2].strip()
            
            if not channel_identifier.startswith("@") and not channel_identifier.lstrip("-").isdigit():
                channel_identifier = f"@{channel_identifier}"
            
            user_data.pop(user_id, None)
            
            if target == 'all': users = await get_all_user_ids()
            elif target == 'vip': users = await get_all_vip_user_ids()
            elif target == 'regular': users = await get_all_regular_user_ids()
            else: users = []
            
            broadcast_info = {
                'from_chat_id': channel_identifier, 
                'message_id': post_id       
            }
            
            await message.answer(f"🔄 Forward boshlanmoqda...\n📢 Kanal: {channel_identifier}\n🔢 Post ID: {post_id}")
            asyncio.create_task(background_broadcast(message, users, broadcast_info))
            
        except ValueError:
            await message.answer("❌ Post ID raqam bo'lishi kerak!\nMasalan: @Anilordtv/1326")
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")

    # --- KANALGA POST QILISH ---
    elif action == 'post_to_channel':
        code = message.text.strip()
        kino = await get_kino_by_code(code)
        if not kino:
            await message.answer("❌ Kod topilmadi.")
            return

        if not MAIN_CHANNELS:
            await message.answer("❌ Asosiy kanal belgilanmagan!", reply_markup=admin_panel_keyboard())
            user_data.pop(user_id, None)
            return

        user_data[user_id] = {
            'action': 'post_channel_select',
            'code': code,
            'selected_channels': set()
        }

        keyboard = await generate_channel_selection_keyboard(user_id, code)

        await message.answer(
            f"🎬 Anime: *{kino.get('title', '''Noma'lum''')}*\n\n"
            f"📡 Qaysi asosiy kanal(lar)ga post qilmoqchisiz? Tanlang:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    # --- BAN/UNBAN ---
    elif action == 'ban_user':
        try:
            ban_id = int(message.text.strip())
            if ban_id in ADMINS:
                await message.answer("❌ Adminlarni ban qilib bo'lmaydi!")
                return
            await ban_user(ban_id, "Admin tomonidan ban qilindi")
            user_data.pop(user_id, None)
            await message.answer(f"✅ Foydalanuvchi {ban_id} ban qilindi!", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'unban_user':
        try:
            unban_id = int(message.text.strip())
            await unban_user(unban_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Foydalanuvchi {unban_id} ban dan chiqarildi!", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'add_users':
        try:
            lines = message.text.strip().split('\n')
            user_ids = []
            for line in lines:
                try:
                    user_ids.append(int(line.strip()))
                except:
                    continue
            if len(user_ids) > 2500:
                await message.answer(f"❌ Maksimal 2500 ta ID qo'shish mumkin! Siz {len(user_ids)} ta yubordingiz.")
                return
            if not user_ids:
                await message.answer("❌ Hech qanday to'g'ri ID topilmadi!")
                return
            await add_multiple_users(user_ids)
            user_data.pop(user_id, None)
            await message.answer(f"✅ {len(user_ids)} ta foydalanuvchi muvaffaqiyatli qo'shildi!", reply_markup=admin_panel_keyboard())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")

    elif action == 'anime_status_code':
        if message.text == "🔙 Orqaga":
            return
        code = message.text.strip()
        anime = await get_kino_by_code(code)
        if not anime:
            await message.answer("❌ Bu kod bilan anime topilmadi!")
            return
        forward_enabled = await get_anime_forward_status(code)
        status_text = "✅ ON" if forward_enabled else "❌ OFF"
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ ON qilish", callback_data=f"anime_fwd_on:{code}"),
            InlineKeyboardButton("❌ OFF qilish", callback_data=f"anime_fwd_off:{code}")
        )
        await message.answer(
            f"🎬 Anime: {anime['title']}\nStatus: {status_text}\nForward statusini o\'zgartiring:",
            reply_markup=kb
        )
        user_data.pop(message.from_user.id, None)

    # --- АРНАЙЫ ІЗДЕУ (ТЕК КНОПКАМЕН КІРГЕНДЕ) ---

    # 1. САНМЕН ІЗДЕУ
    elif action == 'search_by_code':
        code = message.text.strip()
        if not code.isdigit():
            await message.answer("❌ Iltimos, faqat raqam (kod) kiriting.")
            return

        kino = await get_kino_by_code(code)
        if kino:
            unsubscribed = await get_unsubscribed_channels(user_id)
            if unsubscribed:
                markup = await make_unsubscribed_markup(user_id, code)
                await message.answer("❗ Animeni olishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
            else:
                await increment_stat(code, "init")
                await increment_stat(code, "searched")
                await send_reklama_post(user_id, code)
                user_data.pop(user_id, None) 
        else:
            await message.answer("❌ Bu kod topilmadi.")

    # 2. АТЫМЕН ІЗДЕУ
    elif action == 'search_by_name':
        query = message.text.strip()
        if len(query) < 2:
            await message.answer("❌ Qisqa nom. To'liqroq yozing.")
            return

        results = await search_anime_by_name(query, limit=20)
        if results:
            kb = InlineKeyboardMarkup(row_width=1)
            for anime in results:
                kb.add(InlineKeyboardButton(f"{anime['title']}", callback_data=f"select_anime:{anime['code']}"))
            await message.answer(f"🔎 {len(results)} ta anime topildi:", reply_markup=kb)
            user_data.pop(user_id, None)
        else:
            await message.answer("❌ Hech narsa topilmadi.")

    # --- ТҮЗЕТУ: Чатқа жай жазса, бот жауап бермейді ---
    else:
        pass
        # handler_all_message tugadi
@dp.callback_query_handler(lambda c: c.data.startswith("anime_fwd_"))
async def anime_forward_toggle_callback(call: types.CallbackQuery):
    parts = call.data.split(":")
    action = parts[0]
    code = parts[1]

    if action == "anime_fwd_on":
        await set_anime_forward_status(code, True)
        await call.message.edit_text("✅ Anime forward statusi ON qilindi!")
    elif action == "anime_fwd_off":
        await set_anime_forward_status(code, False)
        await call.message.edit_text("❌ Anime forward statusi OFF qilindi!")

    await call.answer()
             # POST QILISH
# --- YANGI HANDLER (Kanal tanlash menyusini boshqarish) ---
@dp.callback_query_handler(lambda c: c.data.startswith("post_"))
async def post_selection_callback(call: types.CallbackQuery):
    user_id = call.from_user.id

    # 1. Callback-тан 'action' мен 'code'-ты аламыз
    parts = call.data.split(":")
    action_part = parts[0]

    try:
        if action_part == "post_toggle_ch":
            # post_toggle_ch:CHANNEL_ID:CODE
            code = parts[2]
        else:
            # post_send_all:CODE
            # post_send_selected:CODE
            # post_cancel:CODE
            code = parts[1]
    except IndexError:
        await call.answer("❌ Xatolik! (Eski tugma). /start bosing.", show_alert=True)
        return

    # 2. 'user_data'-ны аламыз
    data = user_data.get(user_id, {})

    # 3. 'state' (жағдайды) сақтауды қажет ететін әрекеттерді тексереміз
    if action_part in ["post_toggle_ch", "post_send_selected"]:

        # ЕГЕР STATE (ЖАҒДАЙ) ЖОҒАЛЫП КЕТСЕ (REPLIT RESTART):
        if data.get('action') != 'post_channel_select':

            # Тексеру: Бұл админ бе?
            if user_id in ADMINS:
                print(f"[DEBUG] Holat yo'qolgan. {user_id} uchun 'post_channel_select' qayta tiklanmoqda...")

                # Жоғалған 'state'-ті ҚАЛПЫНА КЕЛТІРУ
                user_data[user_id] = {
                    'action': 'post_channel_select',
                    'code': code,
                    'selected_channels': set() # Таңдаулар басынан басталады
                }

                # Функцияны тоқтатып, пайдаланушыға қайта басуды сұраймыз
                await call.answer("🔄 Holat qayta tiklandi. Iltimos, qaytadan bosing.", show_alert=False)
                return

            else:
                # Егер админ болмаса (мүмкін емес, бірақ...) қате шығарамыз
                try:
                    await call.message.edit_text("❌ Xatolik! Yoki vaqt tugadi. /start bosing.")
                except: pass
                await call.answer("❌ Xatolik! Yoki vaqt tugadi.", show_alert=True)
                return

        # Егер state орнында болса, 'data' айнымалысын жаңартамыз (маңызды!)
        data = user_data.get(user_id, {})


    # --- Әрекеттерді өңдеу ---

    if action_part == "post_toggle_ch":
        try:
            channel_id = int(parts[1])

            # 'selected_channels' бар-жоғын тексереміз (жаңадан құрылған болуы мүмкін)
            if 'selected_channels' not in data:
                 data['selected_channels'] = set() # Егер жоқ болса, жаңасын жасаймыз

            if channel_id in data['selected_channels']:
                data['selected_channels'].remove(channel_id)
                await call.answer(f"ID: {channel_id} olib tashlandi")
            else:
                data['selected_channels'].add(channel_id)
                await call.answer(f"ID: {channel_id} tanlandi")

            # Клавиатураны жаңартқанда 'code'-ты қайта береміз
            new_kb = await generate_channel_selection_keyboard(user_id, code)
            await call.message.edit_reply_markup(reply_markup=new_kb)

        except Exception as e:
            print(f"post_toggle_ch xatolik: {e}")
            await call.answer("❌ Xatolik!")

    elif action_part == "post_send_all" or action_part == "post_send_selected":

        target_channels = []
        if action_part == "post_send_all":
            target_channels = MAIN_CHANNELS
            await call.answer("📤 Barcha kanallarga yuborilmoqda...")
        else: # post_send_selected
            # Бұл бөлік 'user_data'-ға тәуелді
            target_channels = list(data.get('selected_channels', []))
            if not target_channels:
                await call.answer("❌ Hech qaysi kanal tanlanmadi!", show_alert=True)
                return
            await call.answer(f"📤 {len(target_channels)} ta tanlangan kanalga yuborilmoqda...")

        # 'code' енді 'user_data'-дан емес, батырмадан алынды
        kino = await get_kino_by_code(code)
        if not kino:
            await call.message.edit_text("❌ Anime kodi topilmadi! (o'chirilgan bo'lishi mumkin)")
            user_data.pop(user_id, None)
            return

        try:
            await call.message.edit_text(f"📤 Post yuborilmoqda... Jami: {len(target_channels)} ta kanal.")
        except:
            pass # Xabar o'zgarmagan bo'lsa

        success_count = 0
        failed_count = 0

        for channel_id in target_channels:
            try:
                await send_channel_post(channel_id, kino, code)
                success_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed_count += 1
                print(f"Kanalga post yuborishda xatolik ({channel_id}): {e}")

        await call.message.answer(
            f"✅ Yuborish tugadi!\n\n"
            f"👍 Muvaffaqiyatli: {success_count} ta kanal\n"
            f"👎 Xatolik: {failed_count} ta kanal",
            reply_markup=admin_panel_keyboard()
        )
        user_data.pop(user_id, None) # Жағдайды тазалау

    elif action_part == "post_cancel":
        user_data.pop(user_id, None)
        await call.message.edit_text("Post qilish bekor qilindi.")
        await call.answer()
# --- YANGI HANDLER TUGADI ---

async def on_startup(dp):
    await init_db()
    await load_channels()
    admins = await get_all_admins()
    ADMINS.update(admins)
    #salom
    print("Bot ishga tushdi!")

# --- ОСЫ БЛОКТЫ ТОЛЫҒЫМЕН АЛМАСТЫРЫҢЫЗ ---
if __name__ == '__main__':
    # Logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    dp.middleware.setup(ActivityMiddleware())

    # Flask server (Replit uchun)
    if FLASK_AVAILABLE and callable(run_flask_app):
        flask_thread = Thread(target=run_flask_app, daemon=True)
        flask_thread.start()

    print("🚀 Bot ishga tushmoqda...")
    
    try:
        # skip_updates=True eski xabarlarni o'tkazib yuboradi (tezroq yonadi)
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi! (Muvaffaqiyatli o'chirildi)")
    except Exception as e:
        print(f"❌ Kutilmagan xatolik: {e}")
# --- АЛМАСТЫРЫЛАТЫН БЛОКТЫҢ СОҢЫ ---