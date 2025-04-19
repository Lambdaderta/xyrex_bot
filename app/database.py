import aiosqlite
from datetime import datetime, timedelta
import json
from config import XYREX_ID, CHANNEL_ID, TOPIC_ID


DATABASE = 'bans.db'


async def create_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                ban_until TIMESTAMP NOT NULL,
                reason TEXT DEFAULT 'No reason specified'
            )
        ''')
        # Таблица для ПБ
        await db.execute('''
            CREATE TABLE IF NOT EXISTS proofbattles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                names JSON NOT NULL,
                verses JSON NOT NULL,
                tags JSON NOT NULL,
                formatbattla TEXT NOT NULL,
                rules TEXT NOT NULL,
                media1_type TEXT NOT NULL,
                media1_id TEXT NOT NULL,
                media2_type TEXT NOT NULL,
                media2_id TEXT NOT NULL,
                text TEXT NOT NULL,
                pbsher INTEGER NOT NULL,
                username TEXT NOT NULL
            )
        ''')
        
        # Таблица для мнений
        await db.execute('''
            CREATE TABLE IF NOT EXISTS opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opinion_type TEXT NOT NULL,
                name TEXT NOT NULL,
                versus TEXT NOT NULL,
                uslovie TEXT NOT NULL,
                formatbattla TEXT NOT NULL,
                media_list JSON NOT NULL,
                author JSON NOT NULL,
                text TEXT NOT NULL,
                username TEXT NOT NULL,
                mod_message_ids JSON
            )
        ''')
        
        # Таблица очереди с правильными полями
        await db.execute('''
            CREATE TABLE IF NOT EXISTS post_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_type TEXT NOT NULL,
                db_post_id INTEGER NOT NULL,  -- Ссылка на ID в БД
                scheduled_time TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'pending',
                moderation_message_ids TEXT NOT NULL,  -- IDs из канала модерации
                attempts INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def add_ban(user_id: int, duration: int = 86400, reason: str = "No reason"):
    ban_until = datetime.now() + timedelta(seconds=duration)
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            INSERT OR REPLACE INTO bans (user_id, ban_until, reason)
            VALUES (?, ?, ?)
        ''', (user_id, ban_until.timestamp(), reason))
        await db.commit()


async def remove_ban(user_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM bans WHERE user_id = ?', (user_id,))
        await db.commit()


async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute('SELECT ban_until FROM bans WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        
        if result:
            ban_until = datetime.fromtimestamp(result[0])
            if datetime.now() > ban_until:
                await remove_ban(user_id)
                return False
            return True
    return False


async def get_ban_info(user_id: int) -> dict:
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute('SELECT ban_until, reason FROM bans WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        
        if result:
            return {
                'ban_until': datetime.fromtimestamp(result[0]),
                'reason': result[1]
            }
    return None


async def get_all_bans() -> list:
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute('SELECT user_id, ban_until, reason FROM bans')
        rows = await cursor.fetchall()
        return [
            {
                'user_id': row[0],
                'ban_until': datetime.fromtimestamp(row[1]),
                'reason': row[2]
            } for row in rows
        ]


async def cleanup_expired_bans():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM bans WHERE ban_until < ?', (datetime.now().timestamp(),))
        await db.commit()


async def add_to_queue(post_type: str, db_post_id: int, moderation_message_ids: list):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute('''
            SELECT MAX(scheduled_time) FROM post_queue WHERE status = 'pending'
        ''')
        last_time = await cursor.fetchone()
        next_time = datetime.now() + timedelta(minutes=1)
        
        if last_time[0]:
            last_time = datetime.fromtimestamp(last_time[0])
            next_time = max(next_time, last_time + timedelta(minutes=1))
        
        await db.execute('''
            INSERT INTO post_queue (
                post_type,
                db_post_id,
                moderation_message_ids,
                scheduled_time
            ) VALUES (?, ?, ?, ?)
        ''', (
            post_type,
            db_post_id,
            json.dumps(moderation_message_ids),
            next_time.timestamp()
        ))
        await db.commit()


async def get_next_post():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute('''
            SELECT * FROM post_queue 
            WHERE status = 'pending' 
            AND scheduled_time <= ?
            ORDER BY scheduled_time 
            LIMIT 1
        ''', (datetime.now().timestamp(),))
        
        return await cursor.fetchone()


async def update_post(post_id: int, status: str):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            UPDATE post_queue 
            SET status = ?, 
                attempts = attempts + 1 
            WHERE id = ?
        ''', (status, post_id))
        await db.commit()


async def cleanup_queue():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            DELETE FROM post_queue 
            WHERE scheduled_time < ?
        ''', ((datetime.now() - timedelta(days=3)).timestamp(),))
        await db.commit()