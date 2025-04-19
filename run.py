import asyncio
import json
import aiosqlite
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.handlers import router
from app.database import create_db, cleanup_expired_bans, cleanup_queue, get_next_post, update_post
from config import TOKEN, XYREX_ID, CHANNEL_ID, TOPIC_ID
from aiogram.enums import ParseMode
from datetime import datetime
import logging


DATABASE = 'bans.db'


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


async def publish_posts():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT * FROM post_queue 
            WHERE status = 'pending' 
            AND scheduled_time <= ?
            ORDER BY scheduled_time 
            LIMIT 1
        ''', (datetime.now().timestamp(),))
        post = await cursor.fetchone()
        
        if not post:
            return
        
        post_dict = dict(post)
        try:
            if post_dict['post_type'] == 'pb':
                pb_cursor = await db.execute('''
                    SELECT * FROM proofbattles WHERE id = ?
                ''', (post_dict['db_post_id'],))
                pb_data = await pb_cursor.fetchone()
                pb = dict(pb_data)
                
                media_group = [
                    types.InputMediaPhoto(media=pb['media1_id']) if pb['media1_type'] == 'photo' 
                    else types.InputMediaVideo(media=pb['media1_id']),
                    types.InputMediaPhoto(media=pb['media2_id']) if pb['media2_type'] == 'photo' 
                    else types.InputMediaVideo(media=pb['media2_id'])
                ]
                media_group[0].caption = pb['text']
                media_group[0].parse_mode = ParseMode.HTML
                
                await bot.send_media_group(
                    chat_id=XYREX_ID,
                    media=media_group
                )
                await bot.send_poll(
                    chat_id=XYREX_ID,
                    question='⚔️ОБСУЖДЕНИЕ БАТТЛА⚔️',
                    options=json.loads(pb['names']),
                    is_anonymous=True
                )
                
            elif post_dict['post_type'] == 'opinion':
                opinion_cursor = await db.execute('''
                    SELECT * FROM opinions WHERE id = ?
                ''', (post_dict['db_post_id'],))
                opinion_data = await opinion_cursor.fetchone()
                opinion = dict(opinion_data)
                
                media_list = json.loads(opinion['media_list'])
                media_group = []
                for media in media_list:
                    if media[0] == 'photo':
                        media_group.append(types.InputMediaPhoto(media=media[1]))
                    else:
                        media_group.append(types.InputMediaVideo(media=media[1]))
                
                media_group[0].caption = opinion['text']
                media_group[0].parse_mode = ParseMode.HTML
                
                await bot.send_media_group(
                    chat_id=XYREX_ID,
                    media=media_group
                )
            
            # moderation_ids = json.loads(post_dict['moderation_message_ids'])
            # for msg_id in list(map(int, moderation_ids)):
            #     await bot.delete_message(CHANNEL_ID, msg_id)
            
            await db.execute('''
                UPDATE post_queue 
                SET status = 'published' 
                WHERE id = ?
            ''', (post_dict['id'],))
            await db.commit()
            
        except Exception as e:
            await db.execute('''
                UPDATE post_queue 
                SET status = 'failed', 
                    attempts = attempts + 1 
                WHERE id = ?
            ''', (post_dict['id'],))
            await db.commit()
            logger.error(f"Ошибка публикации: {str(e)}")




async def scheduled_tasks():
    while True:
        await publish_posts()
        await asyncio.sleep(10)  


async def main():
    await create_db()
    
    asyncio.create_task(scheduled_tasks())
    asyncio.create_task(cleanup_expired_bans())
    asyncio.create_task(cleanup_queue())
    
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
    finally:
        scheduler.shutdown()