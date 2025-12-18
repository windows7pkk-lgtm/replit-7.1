# database.py (YARATUCHI @cryosky) papka Raplit 6.9

import asyncpg
import os
import json
import asyncio
from dotenv import load_dotenv
from datetime import date, datetime, timedelta

load_dotenv()

db_pool: asyncpg.pool.Pool | None = None


async def init_db(retries: int = 5, delay: int = 2):
    global db_pool
    for i in range(retries):
        try:
            db_pool = await asyncpg.create_pool(
                dsn=os.getenv("DATABASE_URL"),
                statement_cache_size=0
            )
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        balance INTEGER DEFAULT 0,
                        is_vip BOOLEAN DEFAULT FALSE,
                        vip_until DATE,
                        vip_count INTEGER DEFAULT 0,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                try:
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance INTEGER DEFAULT 0")
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_vip BOOLEAN DEFAULT FALSE")
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS vip_until DATE")
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS vip_count INTEGER DEFAULT 0")
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    
                    # --- МЫНА ЕКІ ЖОЛДЫ ҚОСЫҢЫЗ ---
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT")
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT")
                    # ------------------------------

                except Exception as e:
                    pass
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS kino_codes (
                        code TEXT PRIMARY KEY,
                        title TEXT,
                        channel TEXT,
                        message_id INTEGER,
                        post_count INTEGER,
                        poster_file_id TEXT,
                        caption TEXT,
                        parts_file_ids TEXT,
                        media_type TEXT DEFAULT 'photo',
                        button_text TEXT,
                        button_url TEXT,
                        genre TEXT DEFAULT 'Anime',
                        forward_enabled BOOLEAN DEFAULT TRUE,
                        channel_username TEXT,
                        ovoz_berdi TEXT
                    );
                """)
                
                try:
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS media_type TEXT DEFAULT 'photo'")
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS button_text TEXT")
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS button_url TEXT")
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS genre TEXT DEFAULT 'Anime'")
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS forward_enabled BOOLEAN DEFAULT TRUE")
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS channel_username TEXT")
                    await conn.execute("ALTER TABLE kino_codes ADD COLUMN IF NOT EXISTS ovoz_berdi TEXT")
                except:
                    pass
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS stats (
                        code TEXT PRIMARY KEY,
                        searched INTEGER DEFAULT 0,
                        viewed INTEGER DEFAULT 0
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        user_id BIGINT PRIMARY KEY
                    );
                """)
                
                admin_env = os.getenv("ADMIN_IDS", "")
                default_admins = []
                
                if admin_env:
                    try:
                        default_admins = [int(x.strip()) for x in admin_env.split(",") if x.strip().isdigit()]
                    except:
                        pass

                for admin_id in default_admins:
                    await conn.execute(
                        "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                        admin_id
                    )
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS channels (
                        id SERIAL PRIMARY KEY,
                        channel_id BIGINT NOT NULL,
                        channel_link TEXT NOT NULL,
                        channel_type TEXT NOT NULL,
                        channel_username TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                try:
                    await conn.execute("ALTER TABLE channels ADD COLUMN IF NOT EXISTS channel_username TEXT")
                except:
                    pass
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                """)
                
                await conn.execute("""
                    INSERT INTO bot_settings (key, value) VALUES ('bot_active', 'true')
                    ON CONFLICT (key) DO NOTHING
                """)
                
                await conn.execute("""
                    INSERT INTO bot_settings (key, value) VALUES ('card_number', '8600 0000 0000 0000')
                    ON CONFLICT (key) DO NOTHING
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS banned_users (
                        user_id BIGINT PRIMARY KEY,
                        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reason TEXT
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vip_prices (
                        tariff TEXT PRIMARY KEY,
                        price INTEGER NOT NULL,
                        days INTEGER NOT NULL
                    );
                """)
                
                await conn.execute("""
                    INSERT INTO vip_prices (tariff, price, days) VALUES ('1month', 15000, 30)
                    ON CONFLICT (tariff) DO NOTHING
                """)
                await conn.execute("""
                    INSERT INTO vip_prices (tariff, price, days) VALUES ('3month', 40000, 90)
                    ON CONFLICT (tariff) DO NOTHING
                """)
                await conn.execute("""
                    INSERT INTO vip_prices (tariff, price, days) VALUES ('6month', 70000, 180)
                    ON CONFLICT (tariff) DO NOTHING
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS payment_requests (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        photo_file_id TEXT,
                        amount INTEGER,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS pending_join_requests (
                        user_id BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL,
                        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, channel_id)
                    );
                """)
                
                # --- AI LOG TIZIMI ---
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ai_logs (
                        id SERIAL PRIMARY KEY,
                        action_type TEXT,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
            print("[DB] Ulanish muvaffaqiyatli")
            break
        except Exception as e:
            print(f"[DB] Ulanish xatosi ({i+1}/{retries}): {e}")
            if i + 1 == retries:
                raise
            await asyncio.sleep(delay)


async def get_conn() -> asyncpg.pool.Pool:
    global db_pool
    if db_pool is None:
        await init_db()
        return db_pool
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1;")
    except (asyncpg.InterfaceError, asyncpg.PostgresError):
        print("[DB] Pool uzildi, qayta ulanmoqda…")
        await init_db()
    return db_pool


# Енді 3 зат қабылдайды: user_id, full_name, username
async def add_user(user_id, full_name, username):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, full_name, username, last_active) 
            VALUES ($1, $2, $3, NOW()) 
            ON CONFLICT (user_id) DO UPDATE SET last_active=NOW(), full_name=$2, username=$3
        """, user_id, full_name, username)


async def update_user_activity(user_id):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = $1
        """, user_id)


async def get_user_count():
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) FROM users")
        return row[0]


async def get_today_users():
    pool = await get_conn()
    async with pool.acquire() as conn:
        today = date.today()
        row = await conn.fetchrow("""
            SELECT COUNT(*) FROM users WHERE DATE(created_at) = $1
        """, today)
        return row[0] if row else 0


async def get_active_today_users():
    pool = await get_conn()
    async with pool.acquire() as conn:
        today = date.today()
        row = await conn.fetchrow("""
            SELECT COUNT(*) FROM users WHERE DATE(last_active) = $1
        """, today)
        return row[0] if row else 0


async def get_weekly_new_users():
    pool = await get_conn()
    async with pool.acquire() as conn:
        week_ago = date.today() - timedelta(days=7)
        row = await conn.fetchrow("""
            SELECT COUNT(*) FROM users WHERE DATE(created_at) >= $1
        """, week_ago)
        return row[0] if row else 0


async def get_user_profile(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT balance, is_vip, vip_until, vip_count
            FROM users WHERE user_id = $1
        """, user_id)
        if row:
            return dict(row)
        return {'balance': 0, 'is_vip': False, 'vip_until': None, 'vip_count': 0}


async def update_user_balance(user_id: int, amount: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, balance) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET balance = users.balance + $2
        """, user_id, amount)


async def set_user_balance(user_id: int, amount: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, balance) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET balance = $2
        """, user_id, amount)


async def give_vip(user_id: int, days: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT vip_until, vip_count FROM users WHERE user_id = $1", user_id)
        
        if row and row['vip_until']:
            if row['vip_until'] > date.today():
                new_vip_until = row['vip_until'] + timedelta(days=days)
            else:
                new_vip_until = date.today() + timedelta(days=days)
        else:
            new_vip_until = date.today() + timedelta(days=days)
        
        vip_count = (row['vip_count'] if row else 0) + 1
        
        await conn.execute("""
            INSERT INTO users (user_id, is_vip, vip_until, vip_count)
            VALUES ($1, TRUE, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                is_vip = TRUE,
                vip_until = $2,
                vip_count = $3
        """, user_id, new_vip_until, vip_count)


async def remove_vip(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET is_vip = FALSE, vip_until = NULL
            WHERE user_id = $1
        """, user_id)
# database.py (TUZATILGAN)
async def is_user_vip(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT is_vip, vip_until FROM users WHERE user_id = $1
        """, user_id)
        
        if not row:
            return False
        
        if row['is_vip'] and row['vip_until']:
            # SANA FORMATINI TEKSHIRISH VA TO'G'RILASH
            vip_until = row['vip_until']
            
            # Agar datetime bo'lsa, date ga o'tkazamiz
            if isinstance(vip_until, datetime):
                vip_until = vip_until.date()
                
            # Hozirgi sana bilan solishtirish
            if vip_until < date.today():
                await remove_vip(user_id)
                return False
            return True
        
        return False

async def get_all_vip_users():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, vip_until FROM users
            WHERE is_vip = TRUE AND vip_until >= $1
            ORDER BY vip_until DESC
        """, date.today())
        return [dict(row) for row in rows]


async def get_all_vip_user_ids():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id FROM users
            WHERE is_vip = TRUE AND vip_until >= $1
        """, date.today())
        return [row["user_id"] for row in rows]


async def get_all_regular_user_ids():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id FROM users
            WHERE is_vip = FALSE OR vip_until < $1
        """, date.today())
        return [row["user_id"] for row in rows]


async def get_vip_prices():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT tariff, price, days FROM vip_prices ORDER BY days")
        return {row['tariff']: {'price': row['price'], 'days': row['days']} for row in rows}


async def update_vip_price(tariff: str, price: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE vip_prices SET price = $1 WHERE tariff = $2
        """, price, tariff)


async def get_card_number():
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT value FROM bot_settings WHERE key = 'card_number'
        """)
        if row:
            return row['value']
        return '8600 0000 0000 0000'


async def set_card_number(card: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_settings (key, value) VALUES ('card_number', $1)
            ON CONFLICT (key) DO UPDATE SET value = $1
        """, card)


async def add_payment_request(user_id: int, photo_file_id: str, amount: int = None):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO payment_requests (user_id, photo_file_id, amount)
            VALUES ($1, $2, $3)
        """, user_id, photo_file_id, amount)


async def get_pending_payment_requests():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, user_id, photo_file_id, amount, created_at
            FROM payment_requests
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        return [dict(row) for row in rows]


async def approve_payment_request(request_id: int, amount: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT user_id FROM payment_requests WHERE id = $1
        """, request_id)
        
        if row:
            user_id = row['user_id']
            await conn.execute("""
                UPDATE payment_requests SET status = 'approved', amount = $1
                WHERE id = $2
            """, amount, request_id)
            await update_user_balance(user_id, amount)
            return user_id
        return None


async def reject_payment_request(request_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE payment_requests SET status = 'rejected'
            WHERE id = $1
        """, request_id)


async def add_anime(code, title, poster_file_id, parts_file_ids, caption="", media_type="photo", genre="Anime", forward_enabled=True, channel_username="", ovoz_berdi=""):
    pool = await get_conn()
    async with pool.acquire() as conn:
        parts_json = json.dumps(parts_file_ids)
        post_count = len(parts_file_ids)
        
        await conn.execute("""
            INSERT INTO kino_codes (
                code, title, poster_file_id, caption, parts_file_ids, 
                post_count, media_type, genre, forward_enabled, channel_username, 
                ovoz_berdi
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                poster_file_id = EXCLUDED.poster_file_id,
                caption = EXCLUDED.caption,
                parts_file_ids = EXCLUDED.parts_file_ids,
                post_count = EXCLUDED.post_count,
                media_type = EXCLUDED.media_type,
                genre = EXCLUDED.genre,
                forward_enabled = EXCLUDED.forward_enabled,
                channel_username = EXCLUDED.channel_username,
                ovoz_berdi = EXCLUDED.ovoz_berdi;
        """, 
        code, title, poster_file_id, caption, parts_json, post_count, media_type, 
        genre, forward_enabled, channel_username, ovoz_berdi)
        
        await conn.execute("""
            INSERT INTO stats (code) VALUES ($1)
            ON CONFLICT DO NOTHING
        """, code)


async def get_kino_by_code(code):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT code, title, poster_file_id, caption, parts_file_ids,
                   post_count, channel, message_id, media_type, button_text, button_url,
                   genre, forward_enabled, channel_username, ovoz_berdi
            FROM kino_codes
            WHERE code = $1
        """, code)
        if row:
            data = dict(row)
            data["parts_file_ids"] = json.loads(data["parts_file_ids"]) if data.get("parts_file_ids") else []
            return data
        return None


async def get_all_codes():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, poster_file_id, caption, parts_file_ids,
                   post_count, channel, message_id, media_type, button_text, button_url,
                   genre, forward_enabled, channel_username, ovoz_berdi
            FROM kino_codes
        """)
        result = []
        for row in rows:
            item = dict(row)
            item["parts_file_ids"] = json.loads(item["parts_file_ids"]) if item.get("parts_file_ids") else []
            result.append(item)
        return result


async def delete_kino_code(code):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM stats WHERE code = $1", code)
        result = await conn.execute("DELETE FROM kino_codes WHERE code = $1", code)
        return result.endswith("1")


async def increment_stat(code, field):
    if field not in ("searched", "viewed", "init"):
        return
    pool = await get_conn()
    async with pool.acquire() as conn:
        if field == "init":
            await conn.execute("""
                INSERT INTO stats (code, searched, viewed) VALUES ($1, 0, 0)
                ON CONFLICT DO NOTHING
            """, code)
        else:
            result = await conn.execute(f"""
                UPDATE stats SET {field} = COALESCE({field}, 0) + 1 WHERE code = $1
            """, code)
            if result == 'UPDATE 0':
                await conn.execute(f""" 
                    INSERT INTO stats (code, searched, viewed) VALUES ($1, $2, $3)
                    ON CONFLICT (code) DO UPDATE SET {field} = stats.{field} + 1
                """, code, 1 if field == "searched" else 0, 1 if field == "viewed" else 0)


async def get_code_stat(code):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT searched, viewed FROM stats WHERE code = $1", code
        )
        return row


async def update_anime_code(old_code, new_code, new_title):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE kino_codes SET code = $1, title = $2 WHERE code = $3
        """, new_code, new_title, old_code)


async def get_all_admins():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM admins")
        return {row["user_id"] for row in rows}


async def add_admin(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id
        )


async def remove_admin(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM admins WHERE user_id = $1", user_id)


async def get_all_user_ids():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users")
        return [row["user_id"] for row in rows]


async def add_part_to_anime(code: str, file_id: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT parts_file_ids FROM kino_codes WHERE code=$1", code)
        raw_parts_json = row["parts_file_ids"]
        
        if raw_parts_json is None:
            parts = []
        else:
            try:
                parts = json.loads(raw_parts_json)
                if not isinstance(parts, list):
                    parts = []
            except:
                parts = []

        parts.append(file_id)
        await conn.execute(
            "UPDATE kino_codes SET parts_file_ids=$1, post_count=$2 WHERE code=$3",
            json.dumps(parts),
            len(parts),
            code
        )


async def delete_part_from_anime(code: str, part_number: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT parts_file_ids FROM kino_codes WHERE code=$1", code)
        if not row or not row["parts_file_ids"]:
            return False
        parts = json.loads(row["parts_file_ids"])
        if part_number < 1 or part_number > len(parts):
            return False
        parts.pop(part_number - 1)
        await conn.execute(
            "UPDATE kino_codes SET parts_file_ids=$1, post_count=$2 WHERE code=$3",
            json.dumps(parts),
            len(parts),
            code
        )
        return True


async def search_anime_by_name(query: str, limit: int = 10):
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, post_count
            FROM kino_codes
            WHERE LOWER(title) LIKE LOWER($1)
            LIMIT $2
        """, f"%{query}%", limit)
        return [dict(row) for row in rows]


async def update_anime_poster(code, poster_file_id, caption, media_type, button_text=None, button_url=None):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE kino_codes 
            SET poster_file_id = $1, caption = $2, media_type = $3, button_text = $4, button_url = $5 
            WHERE code = $6
        """, poster_file_id, caption, media_type, button_text, button_url, code)


async def add_channel_to_db(channel_id: int, channel_link: str, channel_type: str, channel_username: str = ""):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO channels (channel_id, channel_link, channel_type, channel_username)
            VALUES ($1, $2, $3, $4)
        """, channel_id, channel_link, channel_type, channel_username)


async def get_channels_by_type(channel_type: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT channel_id, channel_link, channel_username FROM channels WHERE channel_type = $1
        """, channel_type)
        return [(row['channel_id'], row['channel_link'], row['channel_username']) for row in rows]
        
async def delete_channel_from_db(channel_id: int, channel_type: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM channels WHERE channel_id = $1 AND channel_type = $2
        """, channel_id, channel_type)
        
        if channel_type == 'sub':
            try:
                await conn.execute("""
                    DELETE FROM pending_join_requests WHERE channel_id = $1
                """, channel_id)
            except Exception as e:
                print(f"[DB] Zayavka o'chirish xatosi: {e}")


async def set_bot_active(is_active: bool):
    pool = await get_conn()
    async with pool.acquire() as conn:
        value = 'true' if is_active else 'false'
        await conn.execute("""
            INSERT INTO bot_settings (key, value) VALUES ('bot_active', $1)
            ON CONFLICT (key) DO UPDATE SET value = $1
        """, value)


async def get_bot_active():
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT value FROM bot_settings WHERE key = 'bot_active'
        """)
        if row:
            return row['value'] == 'true'
        return True


async def ban_user(user_id: int, reason: str = ""):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO banned_users (user_id, reason) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET reason = $2
        """, user_id, reason)


async def unban_user(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM banned_users WHERE user_id = $1
        """, user_id)


async def is_user_banned(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT user_id FROM banned_users WHERE user_id = $1
        """, user_id)
        return row is not None


async def get_all_banned_users():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, reason, banned_at FROM banned_users
        """)
        return [dict(row) for row in rows]


async def add_multiple_users(user_ids: list):
    pool = await get_conn()
    async with pool.acquire() as conn:
        for user_id in user_ids:
            await conn.execute("""
                INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING
            """, user_id)


async def set_anime_forward_status(code: str, enabled: bool):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE kino_codes SET forward_enabled = $1 WHERE code = $2
        """, enabled, code)


async def get_anime_forward_status(code: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT forward_enabled FROM kino_codes WHERE code = $1
        """, code)
        return row['forward_enabled'] if row else True


async def update_anime_genre(code: str, genre: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE kino_codes SET genre = $1 WHERE code = $2
        """, genre, code)


async def get_anime_by_genre(genre: str, limit: int = 20):
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, genre, post_count
            FROM kino_codes
            WHERE LOWER(genre) LIKE LOWER($1)
            LIMIT $2
        """, f"%{genre}%", limit)
        return [dict(row) for row in rows]


async def get_all_genres():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT genre FROM kino_codes 
            WHERE genre IS NOT NULL AND genre != ''
        """)
        
        all_genres = set()
        for row in rows:
            raw_genre = row['genre']
            import re
            parts = re.split(r'[,\.\/\s]+', raw_genre) 
            
            for part in parts:
                clean = part.strip().capitalize()
                if len(clean) > 2 and clean.lower() not in ["va", "bilan", "janr"]: 
                    all_genres.add(clean)
        
        return sorted(list(all_genres))


async def get_top_anime(limit: int = 10):
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT k.code, k.title, k.genre, k.post_count, s.viewed
            FROM kino_codes k
            LEFT JOIN stats s ON k.code = s.code
            ORDER BY s.viewed DESC
            LIMIT $1
        """, limit)
        return [dict(row) for row in rows]


async def get_random_anime(limit: int = 1):
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, genre, post_count
            FROM kino_codes
            ORDER BY RANDOM()
            LIMIT $1
        """, limit)
        return [dict(row) for row in rows]


async def add_pending_request(user_id: int, channel_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO pending_join_requests (user_id, channel_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, channel_id) DO UPDATE SET requested_at = CURRENT_TIMESTAMP
        """, user_id, channel_id)


async def is_request_pending(user_id: int, channel_id: int) -> bool:
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT 1 FROM pending_join_requests 
            WHERE user_id = $1 AND channel_id = $2
        """, user_id, channel_id)
        return row is not None


async def remove_all_pending_requests(user_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM pending_join_requests WHERE user_id = $1
        """, user_id)


# --- AI VA LOGLAR UCHUN KERAKLI FUNKSIYALAR (QAYTA TIKLANDI) ---

async def log_ai_action(action_type: str, details: str):
    """AI qilgan ishini bazaga yozib qo'yadi"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO ai_logs (action_type, details) VALUES ($1, $2)", action_type, details)

# --- BACKUP TIZIMI (YANGI) ---

# DateTime-ni JSON uchun to'g'irlash yordamchisi
def date_converter(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)

async def get_full_database_dump():
    """Barcha jadvallarni o'qib, lug'at (dict) qaytaradi"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        data = {}
        
        # 1. Users
        users = await conn.fetch("SELECT * FROM users")
        data['users'] = [dict(u) for u in users]
        
        # 2. Kino Codes
        kinos = await conn.fetch("SELECT * FROM kino_codes")
        data['kino_codes'] = [dict(k) for k in kinos]
        
        # 3. Channels
        channels = await conn.fetch("SELECT * FROM channels")
        data['channels'] = [dict(c) for c in channels]
        
        # 4. Stats
        stats = await conn.fetch("SELECT * FROM stats")
        data['stats'] = [dict(s) for s in stats]
        
        # 5. Vip Prices
        prices = await conn.fetch("SELECT * FROM vip_prices")
        data['vip_prices'] = [dict(p) for p in prices]
        
        return data

async def restore_database_from_dump(data: dict):
    """JSON ma'lumotlarni bazaga yuklaydi"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        
        # 1. USERS
        if 'users' in data and isinstance(data['users'], list):
            for u in data['users']:
                # Agar faqat ID bo'lsa (siz aytgan oddiy ro'yxat)
                if isinstance(u, int): 
                    await conn.execute("INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", u)
                # Agar to'liq user ma'lumoti bo'lsa
                elif isinstance(u, dict):
                    await conn.execute("""
                        INSERT INTO users (user_id, balance, is_vip, vip_until, vip_count, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (user_id) DO UPDATE SET
                            balance = EXCLUDED.balance,
                            is_vip = EXCLUDED.is_vip,
                            vip_until = EXCLUDED.vip_until,
                            vip_count = EXCLUDED.vip_count
                    """, u['user_id'], u.get('balance', 0), u.get('is_vip', False), 
                         # Sana formatini to'g'irlash kerak bo'lishi mumkin, oddiylik uchun str->date o'tkazishni shu yerda qilamiz
                         datetime.fromisoformat(u['vip_until']).date() if u.get('vip_until') else None,
                         u.get('vip_count', 0),
                         datetime.fromisoformat(str(u['created_at'])) if u.get('created_at') else datetime.now()
                    )

        # 2. KINO CODES
        if 'kino_codes' in data:
            for k in data['kino_codes']:
                await conn.execute("""
                    INSERT INTO kino_codes (code, title, poster_file_id, parts_file_ids, post_count, genre, media_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (code) DO UPDATE SET
                        title = EXCLUDED.title,
                        poster_file_id = EXCLUDED.poster_file_id,
                        parts_file_ids = EXCLUDED.parts_file_ids,
                        post_count = EXCLUDED.post_count,
                        genre = EXCLUDED.genre
                """, k['code'], k['title'], k['poster_file_id'], k['parts_file_ids'], k['post_count'], k.get('genre'), k.get('media_type', 'photo'))

        # 3. CHANNELS
        if 'channels' in data:
            for c in data['channels']:
                await conn.execute("""
                    INSERT INTO channels (channel_id, channel_link, channel_type, channel_username)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                """, c['channel_id'], c['channel_link'], c['channel_type'], c.get('channel_username'))

        return True

async def get_full_stat_data():
    """
    # Barcha statistik ma'lumotlarni bitta so'rovda oladi.
    # Bu serverga yuklamani kamaytiradi.
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        # # Hozirgi vaqt va sanalar
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # # So'rovlar (Jami, Bugungi, Haftalik, Oylik)
        
        # # 1. Jami foydalanuvchilar
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        # # 2. Yangi foydalanuvchilar (Created_at bo'yicha)
        new_today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= $1", today_start)
        new_week = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= $1", week_ago)
        new_month = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= $1", month_ago)
        
        # # 3. Aktiv foydalanuvchilar (Last_active bo'yicha)
        active_today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_active >= $1", today_start)
        active_week = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_active >= $1", week_ago)
        active_month = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_active >= $1", month_ago)
        
        # # 4. Jami animelar
        total_anime = await conn.fetchval("SELECT COUNT(*) FROM kino_codes")
        
        # # 5. Bot holati
        bot_active = await get_bot_active()

        return {
            "total_users": total_users,
            "new_today": new_today,
            "active_today": active_today,
            "new_week": new_week,
            "active_week": active_week,
            "new_month": new_month,
            "active_month": active_month,
            "total_anime": total_anime,
            "bot_active": bot_active
        }

async def clean_old_logs():
    """7 kundan eski loglarni o'chiradi"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM ai_logs WHERE created_at < NOW() - INTERVAL '7 days'")

async def get_recent_logs(limit=15):
    """Admin uchun oxirgi loglarni qaytaradi"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT action_type, details, created_at FROM ai_logs ORDER BY created_at DESC LIMIT $1", limit)
        return [dict(row) for row in rows]

async def get_all_anime_list_for_ai():
    """
    AI ga bazadagi barcha animelarni ko'rsatish uchun ro'yxatni oladi.
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, genre FROM kino_codes 
            ORDER BY code ASC
        """)
        
        anime_list = []
        for row in rows:
            line = f"Kod: {row['code']} | Nomi: {row['title']} | Janr: {row['genre']}"
            anime_list.append(line)
            
        return "\n".join(anime_list)