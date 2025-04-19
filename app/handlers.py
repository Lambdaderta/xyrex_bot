# Основные функции бота

# Импорты
from aiogram import F, Router, Bot, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from app.database import add_ban, remove_ban, is_banned, get_all_bans, get_ban_info, add_to_queue
from config import CHANNEL_ID, XYREX_ID, XYREX_ANKETS, TOPIC_ID
import app.keyboards as kb
from app.keyboards import get_publicpb_keyboard, get_opinion_keyboard
import json
import aiosqlite


# Константа


DATABASE = 'bans.db'


# Классы


router = Router()


class Reg(StatesGroup):
    opinion_type = State()
    group_members = State()
    name = State()
    versus = State()
    uslovie = State()
    formatbattla = State()
    load_media = State()
    media_group = State()
    public = State()

class Proofbattle(StatesGroup):
    names = State()
    verses = State()
    tags = State()
    regone = State()
    regtwo = State()
    rules = State()
    confirm = State()
    selectone = State()
    selecttwo = State()


# Баны


def parse_time(time_str: str) -> int:
    time_units = {
        'минут': 60,
        'час': 3600,
        'день': 86400
    }
    for unit, multiplier in time_units.items():
        if unit in time_str:
            return int(time_str.split()[0]) * multiplier
    return 86400


@router.message(CommandStart(), F.chat.type == 'private')
async def cmd_start(message: Message):
    if await is_banned(message.chat.id):
        return await message.reply('Вы были забанены.')
    await message.reply('Привет, желаешь опубликовать мнение или организовать пб?', reply_markup=kb.main)


@router.message(Command("banxr"), F.chat.id == CHANNEL_ID)
async def ban_user(message: Message):
    try:
        args = message.text.split()[1:]
        if not args:
            return await message.answer("Использование: /banxr <ID> [время] [причина]")
        
        user_id = args[0]
        duration = parse_time(' '.join(args[1:-1])) if len(args) > 2 else 86400
        reason = args[-1] if len(args) > 2 else "Без причины"
        
        try:
            await add_ban(int(user_id), duration, reason)
            ban_info = await get_ban_info(int(user_id))
            await message.answer(f"Пользователь {user_id} забанен до {ban_info['ban_until']} по причине: {reason}")
        except ValueError:
            await message.answer("Неверный ID пользователя")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}") 


@router.message(Command("unbanxr"), F.chat.id == CHANNEL_ID)
async def unban_user(message: Message):
    try:
        args = message.text.split()[1:]
        if not args:
            return await message.answer("Использование: /unbanxr <ID>")
        
        try:
            user_id = int(args[0])
            await remove_ban(user_id)
            await message.answer(f"Пользователь {user_id} разбанен")
        except ValueError:
            await message.answer("Неверный ID пользователя")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")  


@router.message(Command("banslist"), F.chat.id == CHANNEL_ID)
async def list_bans(message: Message):
    bans = await get_all_bans()
    
    if not bans:
        return await message.answer("Список забаненных пользователей пуст.")
    
    response = "<b>Забаненные пользователи:</b>\n\n"
    for ban in bans:
        user_id = ban['user_id']
        ban_until = ban['ban_until'].strftime("%d.%m.%Y %H:%M")
        reason = ban['reason']
        response += (
            f"• <b>ID:</b> {user_id}\n"
            f"  <b>До:</b> {ban_until}\n"
            f"  <b>Причина:</b> {reason}\n\n"
        )    
    await message.answer(response, parse_mode=ParseMode.HTML)


# ПБ


@router.callback_query(F.data == 'PB')
async def pbanswer(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        'Введите имена персонажей, по порядку, через запятую, с пробелом, с большой буквы.')
    await state.set_state(Proofbattle.names)


@router.message(Proofbattle.names)
async def pbnames(message: Message, state: FSMContext):
    nameslist = message.text.split(',')
    await state.update_data(names=nameslist)
    await state.set_state(Proofbattle.verses)
    await message.answer(text='Введите названия произведений/версов, по порядку, сначала для 1 персонажа,'
                              ' потом для 2, через запятую, с пробелом, с большой буквы.')


@router.message(Proofbattle.verses)
async def pbverses(message: Message, state: FSMContext):
    verseslist = message.text.split(',')
    await state.update_data(verses=verseslist)
    await state.set_state(Proofbattle.tags)
    await message.answer(text='Введите теги игроков, по порядку, через запятую, с пробелом.')


@router.message(Proofbattle.tags)
async def pbtags(message: Message, state: FSMContext):
    tagslist = message.text.split(',')
    await state.update_data(tags=tagslist)
    await message.answer(text='Выберите формат ПБ.',
                         reply_markup=kb.pbformat)


@router.callback_query(F.data == 'classic_f')
async def five_pb(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Выбранный формат: тактика')
    await state.update_data(formatbattla='https://t.me/c/2235550385/16')
    await callback.message.edit_text(text='Отправьте условия вашего баттла, если таковых нет, напишите "нет"')
    await state.set_state(Proofbattle.rules)


@router.callback_query(F.data == 'hodi_f')
async def five_pb(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Выбранный формат: ходы')
    await state.update_data(formatbattla='https://t.me/c/2235550385/15')
    await callback.message.edit_text(text='Отправьте условия вашего баттла, если таковых нет, напишите "нет"')
    await state.set_state(Proofbattle.rules)


@router.message(Proofbattle.rules)
async def pbtags(message: Message, state: FSMContext, bot: Bot):
    forward_message = await message.forward(chat_id=XYREX_ANKETS)
    forward_message_id = forward_message.message_id
    chat = await bot.get_chat(XYREX_ANKETS)
    message_link = f"https://t.me/{chat.username}/{forward_message_id}"
    await state.update_data(rules=message_link)
    await message.answer(text='Отправьте анкету(регу) сначала первого игрока, обязательно с фото или видео персонажа.')
    await state.set_state(Proofbattle.regone)


@router.message(Proofbattle.regone)
async def pbregs_one(message: Message, state: FSMContext, bot: Bot):
    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id
    else:
        await message.answer("❌ Нужно отправить фото или видео!")
        await state.clear()
        return

    await state.update_data(
        media1_type=media_type,
        media1_id=media_id,
        pbsher=message.from_user.id,
        username=message.from_user.username
    )

    try:
        forward_message = await message.forward(chat_id=XYREX_ANKETS)
        chat = await bot.get_chat(XYREX_ANKETS)
        message_link = f"https://t.me/{chat.username}/{forward_message.message_id}"
        await state.update_data(link_one=message_link)
        await message.answer("✅ Анкета первого игрока принята! Теперь отправьте анкету второго игрока.")
        await state.set_state(Proofbattle.regtwo)
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке анкеты: {str(e)}")
        await state.clear()


@router.message(Proofbattle.regtwo)
async def pbregs_two(message: Message, state: FSMContext, bot: Bot):
    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id
    else:
        await message.answer("❌ Нужно отправить фото или видео!")
        await state.clear()
        return

    await state.update_data(
        media2_type=media_type,
        media2_id=media_id
    )

    try:
        forward_message = await message.forward(chat_id=XYREX_ANKETS)
        chat = await bot.get_chat(XYREX_ANKETS)
        message_link = f"https://t.me/{chat.username}/{forward_message.message_id}"
        await state.update_data(link_two=message_link)
        
        data = await state.get_data()
        caption = f"""
<blockquote><b>ПЕРСОНАЛЬНЫЙ ПРУФ-БАТТЛ</b></blockquote>

Player 1: {data['tags'][0]}
 <b><a href="{data['link_one']}">{data['names'][0]}</a> — «{data['verses'][0]}»</b>


    <b>⋆ V-E-R-S-U-S ⋆</b>
            
 <b><a href="{data['link_two']}">{data['names'][1]}</a> — «{data['verses'][1]}»</b>
<b>Player 2: {data['tags'][1]}</b>


➥「<a href='{data['formatbattla']}'>правила боев</a>」
➥「<a href='https://t.me/xyrex_realm/27510'>список судей</a>」
➥「<a href='https://t.me/Xyrex_Fights/12643'>условия баттла</a>」
"""

        media_group = []
        
        if data['media1_type'] == 'photo':
            media_group.append(types.InputMediaPhoto(media=data["media1_id"], caption=caption, parse_mode=ParseMode.HTML))
        else:
            media_group.append(types.InputMediaVideo(media=data["media1_id"], caption=caption, parse_mode=ParseMode.HTML))
        
        if data['media2_type'] == 'photo':
            media_group.append(types.InputMediaPhoto(media=data["media2_id"]))
        else:
            media_group.append(types.InputMediaVideo(media=data["media2_id"]))
        
        soo = await bot.send_media_group(chat_id=data['pbsher'], media=media_group)
        message_id = [msg.message_id for msg in soo]
        await state.update_data(text=caption)
        await state.update_data(soo_id=message_id[0])
        await bot.send_message(
            chat_id=data['pbsher'],
            text='Все ли верно?\nПри нажатии на галку ПБ отправится на модерацию.',
            reply_markup=kb.accept
        )
        await state.set_state(Proofbattle.selecttwo)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при формировании поста: {str(e)}")
        await state.clear()

    

@router.callback_query(F.data.in_(["right", "wrong"]))
async def five_pb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == 'right':
        try:
            data = await state.get_data()
            
            required_keys = ['media1_id', 'media2_id', 'link_one', 'link_two', 
                            'names', 'verses', 'tags', 'formatbattla', 'text',
                            'pbsher', 'username']
            for key in required_keys:
                if key not in data:
                    raise KeyError(f"Missing required key: {key}")

            async with aiosqlite.connect(DATABASE) as db:
                cursor = await db.execute('''
                    INSERT INTO proofbattles (
                        names, verses, tags, formatbattla, rules,
                        media1_type, media1_id, media2_type, media2_id,
                        text, pbsher, username
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    json.dumps(data['names']),
                    json.dumps(data['verses']),
                    json.dumps(data['tags']),
                    data['formatbattla'],
                    data.get('rules', ''),
                    data.get('media1_type', 'photo'),
                    data['media1_id'],
                    data.get('media2_type', 'photo'),
                    data['media2_id'],
                    data['text'],
                    data['pbsher'],
                    data['username']
                ))
                await db.commit()
                pb_id = cursor.lastrowid

            # Отправка медиагруппы
            media_group = []
            if data.get('media1_type') == 'photo':
                media_group.append(types.InputMediaPhoto(
                    media=data["media1_id"], 
                    caption=data['text'], 
                    parse_mode=ParseMode.HTML
                ))
            else:
                media_group.append(types.InputMediaVideo(
                    media=data["media1_id"], 
                    caption=data['text'], 
                    parse_mode=ParseMode.HTML
                ))

            if data.get('media2_type') == 'photo':
                media_group.append(types.InputMediaPhoto(media=data["media2_id"]))
            else:
                media_group.append(types.InputMediaVideo(media=data["media2_id"]))

            await bot.send_media_group(
                chat_id=CHANNEL_ID, 
                media=media_group, 
                message_thread_id=TOPIC_ID
            )

            await bot.send_poll(
                chat_id=CHANNEL_ID,
                question='⚔️ОБСУЖДЕНИЕ БАТТЛА⚔️\nКто победит по вашему мнению?',
                options=data['names'],
                is_anonymous=True,
                type='regular',
                message_thread_id=TOPIC_ID,
                reply_markup=get_publicpb_keyboard(pb_id)
            )

            await bot.send_message(
                chat_id=CHANNEL_ID,
                message_thread_id=TOPIC_ID,
                text=f'ID пользователя: {data["pbsher"]}\nUsername: @{data["username"]}\nКоманда для бана: /banxr {data["pbsher"]}'
            )

            await callback.message.edit_text('''✅ Ожидайте проверку. Если баттл долго не начинается, обратитесь к организаторам.
Чтобы начать заново, используйте /start''')
            await state.clear()

        except KeyError as e:
            await callback.message.answer(f'❌ Ошибка: {str(e)}')
            await state.clear()

    else:  
        async with aiosqlite.connect(DATABASE) as db:
            data = await state.get_data()
            if 'pb_id' in data:
                await db.execute('DELETE FROM proofbattles WHERE id = ?', (data['pb_id'],))
                await db.commit()
        await callback.answer('Пост отменен')
        await callback.message.edit_text('❌ Пост отменен')
        await state.clear()


@router.callback_query(F.data.startswith("publicpb:"))
async def handle_publicpb(call: CallbackQuery, bot: Bot):
    pb_id = call.data.split(":")[1]
    
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute('SELECT * FROM proofbattles WHERE id = ?', (pb_id,))
        if await cursor.fetchone() is None:
            await call.answer("❌ Баттл не найден")
            return
        
        
        await add_to_queue(
            post_type='pb',
            db_post_id=pb_id,
            moderation_message_ids=[call.message.message_id]
        )


        for msg_id in call.message.message_id:
            try:
                await bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
            except Exception as e:
                print(f"Ошибка удаления сообщения {msg_id}: {e}")
        
        
        await call.answer("✅ ПБ добавлен в очередь")



@router.callback_query(F.data.startswith("nopublic:"))
async def handle_callback(call: CallbackQuery):
    try:
        pb_id = int(call.data.split(":")[1])
        
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('DELETE FROM proofbattles WHERE id = ?', (pb_id,))
            await db.commit()
            
            await call.message.delete()
            await call.answer("🗑 Бой отменен")
            

        


    except Exception as e:
        await call.answer(f"Произошла ошибка {e}, пишите лямбде")


# Обработка мнений


@router.callback_query(F.data == 'mnenie')
async def mnenie_post(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        'Выберите тип мнения:',
        reply_markup=kb.opinion_type_select
    )
    await state.update_data(username=callback.from_user.username)
    await state.set_state(Reg.opinion_type)


@router.callback_query(F.data.in_(['single', 'group']), Reg.opinion_type)
async def process_opinion_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(opinion_type=callback.data)
    if callback.data == 'group':
        await callback.message.answer('Введите теги/ники иггроков через запятую:')
        await state.set_state(Reg.group_members)
    else:
        await callback.message.answer('Введите имя персонажа, про которого хотите опубликовать мнение')
        await state.set_state(Reg.name)


@router.message(Reg.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите имена персонажей/вселенных через запятую:')
    await state.set_state(Reg.versus)


@router.message(Reg.versus)
async def process_versus(message: Message, state: FSMContext):
    versus = '\n'.join([f'➣ {v.strip()}' for v in message.text.split(',')])
    await state.update_data(versus=versus)
    await message.answer('Введите условия баттла:')
    await state.set_state(Reg.uslovie)


@router.message(Reg.uslovie)
async def process_uslovie(message: Message, state: FSMContext):
    await state.update_data(uslovie=message.text)
    await message.answer('Выберите формат баттла', reply_markup=kb.formatselect)
    await state.set_state(Reg.formatbattla)


@router.callback_query(F.data.in_(['pb_format', 'gch', 'discussion_format']), Reg.formatbattla)
async def process_format(callback: CallbackQuery, state: FSMContext):
    format_text = {
        'pb_format': 'пруфбаттл',
        'gch': 'голосовой чат',
        'discussion_format': 'дискуссия'
    }[callback.data]
    await state.update_data()

    await state.update_data(formatbattla=format_text)
    await callback.message.answer('Отправьте фото/видео с персонажем, если такого нет, пришлите обложку произведения')
    await callback.message.delete()
    await state.set_state(Reg.load_media)


@router.message(Reg.group_members)
async def process_group_members(message: Message, state: FSMContext):
    members = [m.strip() for m in message.text.split(',')]
    await state.update_data(members=members)
    await message.answer('Введите имена персонажей, можно и одного')
    await state.set_state(Reg.name)


@router.message(Reg.load_media, F.photo | F.video)
async def process_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    media_type = 'photo' if message.photo else 'video'
    media_id = message.photo[-1].file_id if media_type == 'photo' else message.video.file_id

    if data['opinion_type'] == 'group':
        media_list = data.get('media_list', [])
        media_list.append((media_type, media_id))
        await state.update_data(media_list=media_list)
        
        # Формирование заголовка
        caption = (
            f"<b>⚔️ПЕРСОНАЛЬНАЯ ПОЗИЦИЯ⚔️</b>\n\n"
            f"<b>Авторы мнения — {message.from_user.username}</b>\n\n"
            f"<b><u>{data['name']}</u> аннигилирует всех персонажей из ниже представленных вселенных:</b>\n"
            f"<blockquote><b>{data['versus']}</b></blockquote>\n"
            f"<b>Условия баттла: {data['uslovie']}</b>\n"
            f"<b>Кто-нибудь желает дать ему отпор в формате {data['formatbattla']}?</b>"
        )
        
        
        try:
            media_group = []
            for mt, mid in media_list:
                media = types.InputMediaPhoto(media=mid) if mt == 'photo' else types.InputMediaVideo(media=mid)
                media_group.append(media)
            media_group[0].caption = caption
            media_group[0].parse_mode = ParseMode.HTML
        except:
            pass


        # Сохранение в БД
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute('''
                INSERT INTO opinions (opinion_type, name, versus, uslovie, formatbattla, media_list, author, text, username)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['opinion_type'],
                data['name'],
                data['versus'],
                data['uslovie'],
                data['formatbattla'],
                json.dumps(media_list),
                json.dumps(data.get('members', [])),
                caption,
                message.from_user.username
            ))
            await db.commit()
            opinion_id = cursor.lastrowid
        
        # Отправка в канал модерации
        try:
            sent_media = await bot.send_media_group(
                chat_id=CHANNEL_ID,
                media=media_group,
                message_thread_id=TOPIC_ID
            )
            media_message_ids = [msg.message_id for msg in sent_media]
            
            confirmation_msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                message_thread_id=TOPIC_ID,
                text=f"ID пользователя:1606739624\n"
                     f"Тег: @{message.from_user.username}, ник, если нету тега: {message.from_user.username} Чтобы забанить '/banxr ID'"
                     f"Для разбана '/unbanxr ID'",
                reply_markup=get_opinion_keyboard(opinion_id)
            )
            moderation_message_ids = media_message_ids + [confirmation_msg.message_id]
            
            # Обновление записи 
            await db.execute('''
                UPDATE opinions 
                SET mod_message_ids = ? 
                WHERE id = ?
            ''', (json.dumps(moderation_message_ids), opinion_id))
            await db.commit()
            
        except Exception as e:
            await message.answer(f"Ошибка при отправке на модерацию: {e}. Пишите лямбде (@lyambdadelta).")
            await state.clear()
            return
        
        await message.answer(f"✅ Ожидайте проверку. Если баттл долго не начинается, обратитесь к организаторам.\n"
                             f"Чтобы начать заново, используйте /start.")
        await state.clear()
        
    else:
        caption = (
            f"<b>⚔️ПЕРСОНАЛЬНАЯ ПОЗИЦИЯ⚔️</b>\n\n"
            f"<b> Автор мнения— @{message.from_user.username}</b>\n\n"
            f"<b><u>{data['name']}</u> аннигилирует всех перечисленных:</b>\n"
            f"<blockquote><b>{data['versus']}</b></blockquote>\n"
            f"<b>Условия баттла: {data['uslovie']}</b>\n"
            f"<b>Кто нибудь желает дать ему отпор в формате {data['formatbattla']}?</b>"
        )
        
        try:
            if media_type == 'photo':
                sent_media = await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=media_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=TOPIC_ID
                )
            else:
                sent_media = await bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=media_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=TOPIC_ID
                )

            async with aiosqlite.connect(DATABASE) as db:
                cursor = await db.execute('''
                    INSERT INTO opinions (opinion_type, name, versus, uslovie, formatbattla, media_list, author, text, username, mod_message_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['opinion_type'],
                    data['name'],
                    data['versus'],
                    data['uslovie'],
                    data['formatbattla'],
                    json.dumps([(media_type, media_id)]),
                    json.dumps([message.from_user.username]),
                    caption,
                    message.from_user.username,
                    json.dumps([])
                ))
                await db.commit()
                opinion_id = cursor.lastrowid
            
            confirmation_msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                message_thread_id=TOPIC_ID,
                text=f"ID пользователя:1606739624\n"
                     f"Тег: @{message.from_user.username}, ник, если нету тега: {message.from_user.username} Чтобы забанить '/banxr ID'"
                     f"Для разбана '/unbanxr ID'",
                reply_markup=get_opinion_keyboard(opinion_id)
            )

            moderation_message_ids = [sent_media.message_id, confirmation_msg.message_id]
            async with aiosqlite.connect(DATABASE) as db:
                await db.execute('''
                    UPDATE opinions 
                    SET mod_message_ids = ? 
                    WHERE id = ?
                ''', (json.dumps(moderation_message_ids), opinion_id))
                await db.commit()
            
            
                
        except Exception as e:
            await message.answer(f"Ошибка при отправке на модерацию: {e}")
            await state.clear()
            return
        
        await message.answer(f"✅ Ожидайте проверку. Если баттл долго не начинается, обратитесь к организаторам.\n"
                             f"Чтобы начать заново, используйте /start.")
        await state.clear()


@router.callback_query(F.data.startswith("opinion_confirm:"))
async def handle_opinion_confirm(call: CallbackQuery, bot: Bot):
    opinion_id = call.data.split(":")[1]
    
    async with aiosqlite.connect(DATABASE) as db:
        # Получение данных мнения
        cursor = await db.execute('SELECT mod_message_ids FROM opinions WHERE id = ?', (opinion_id,))
        row = await cursor.fetchone()
        if not row:
            await call.answer("❌ Мнение не найдено")
            return
        
        mod_message_ids = json.loads(row[0])
        
        # Добавление в очередь
        await add_to_queue(
            post_type='opinion',
            db_post_id=opinion_id,
            moderation_message_ids=json.dumps(mod_message_ids)
        )
        
        # Удаление сообщений модерации
        for msg_id in mod_message_ids:
            try:
                await bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
            except Exception as e:
                print(f"Ошибка удаления сообщения {msg_id}: {e}")
        
        await call.answer("✅ Мнение добавлено в очередь")


@router.callback_query(F.data.startswith("opinion_cancel:"))
async def handle_opinion_cancel(call: CallbackQuery, bot: Bot):
    try:
        opinion_id = int(call.data.split(":")[1])
        
        async with aiosqlite.connect(DATABASE) as db:
            # Удаление мнения из БД
            await db.execute('DELETE FROM opinions WHERE id = ?', (opinion_id,))
            
            # Получение message_ids для удаления
            cursor = await db.execute('SELECT mod_message_ids FROM opinions WHERE id = ?', (opinion_id,))
            row = await cursor.fetchone()
            if row:
                mod_message_ids = json.loads(row[0])
                for msg_id in mod_message_ids:
                    try:
                        await bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
                    except Exception as e:
                        print(f"Ошибка удаления сообщения {msg_id}: {e}")
            
            await db.commit()
            await call.answer("🗑 Мнение отменено")
            
    except Exception as e:
        await call.answer(f"Ошибка: {str(e)}")


# @router.callback_query(F.data == "yes")
# async def handle_opinion_yes(call: CallbackQuery, state: FSMContext):
#     data = await state.get_data()
    
#     async with aiosqlite.connect(DATABASE) as db:
#         cursor = await db.execute('''
#             INSERT INTO opinions (
#                 opinion_type, name, versus, uslovie,
#                 formatbattla, media_list, author, username
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             data['opinion_type'],
#             data['name'],
#             data['versus'],
#             data['uslovie'],
#             data['formatbattla'],
#             json.dumps(data.get('media_list', [])),
#             json.dumps(data.get('members', [])),
#             data['username']
#         ))
#         await db.commit()
#         opinion_id = cursor.lastrowid  
    
#     await add_to_queue(
#         post_type='opinion',
#         db_post_id=opinion_id,
#         moderation_message_ids=[call.message.message_id]  
#     )
#     await call.answer("✅ Мнение отправлено на модерацию")
#     await state.clear()


# @router.callback_query(F.data == "no")
# async def handle_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
#     await call.message.delete()
#     await call.answer("❌ Пост отменен")
#     await state.clear()


# data = await state.get_data()
    # await message.answer_photo(
    #     photo=data['photo'],
    #     caption=f'<b>⚔️ Персональная позиция⚔️\n</b>'
    #             f'\n'
    #             f'<b>— @{data["username"]}\n</b>'
    #             f'\n'
    #             f'➥ <b><u>{data["name"]}</u> аннигилирует всех нижеперечисленных персонажей/вселенных:</b>\n'
    #             f'<blockquote><b>{data["versus"]}</b></blockquote>\n'
    #             f'<b>Условия баттла: {data["uslovie"]}</b>\n'
    #             f'<b>Формат: {data["formatbattla"]}</b>',
    #     parse_mode=ParseMode.HTML
    # )

    # data = await state.get_data()
    # await bot.send_photo(
    #     chat_id=CHANNEL_ID,
    #     message_thread_id=TOPIC_ID,
    #     photo=data['photo'],
    #     caption=f'<b>⚔️ Персональная позиция⚔️\n</b>'
    #             f'\n'
    #             f'<b>— @{data["username"]}\n</b>'
    #             f'\n'
    #             f'➥ <b><u>{data["name"]}</u> аннигилирует всех нижеперечисленных персонажей/вселенных:</b>\n'
    #             f'<blockquote><b>{data["versus"]}</b></blockquote>\n'
    #             f'<b>Условия баттла: {data["uslovie"]}</b>\n'
    #             f'<b>Формат: {data["formatbattla"]}</b>',
    #     parse_mode=ParseMode.HTML,
    #     reply_markup=kb.public
    # )
    # user_id = message.from_user.id
    # username = message.from_user.username
    # full_name = message.from_user.full_name
    # await bot.send_message(chat_id=CHANNEL_ID,
    #                        message_thread_id=TOPIC_ID,
    #                        text=f'ID пользователя:{user_id}\n'
    #                             f'Тег: @{username}, ник, если нету тега: {full_name}'
    #                             f'Чтобы забанить "/banxr ID"\n'
    #                             f'Для разбана "/unbanxr ID"')
    # await message.answer(text='Ваше мнение было отправлено на проверку модерации, вам осталось только подождать!\n'
    #                           "Чтобы начать снова, пропишите команду /start")
    # await state.clear()


# @router.callback_query(F.data.in_(["yes", "no"]))
# async def handle_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
#     if call.data == "yes":
#         try:
#             data = await state.get_data()
#             message_ids = [call.message.message_id]
            
#             # Добавляем в очередь с правильными параметрами
#             await add_to_queue(
#                 message_ids=message_ids,
#                 chat_id=CHANNEL_ID,
#                 topic_id=TOPIC_ID,
#                 post_type='opinion',
#                 additional_data=json.dumps(data)
#             )
#             await call.answer("✅ Мнение отправлено на модерацию!")
#         except Exception as e:
#             await call.answer("❌ Ошибка при добавлении в очередь")
#             print(f"Ошибка: {str(e)}")
#     else:
#         await call.message.delete()
#         await call.answer("❌ Пост отменен")
#     await state.clear()