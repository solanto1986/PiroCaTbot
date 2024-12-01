import logging
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest, EditBannedRequest
from telethon.tl.types import ChannelParticipantsSearch, ChatBannedRights

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем данные из переменных окружения
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Проверка значений
if API_ID is None or not API_HASH or not BOT_TOKEN:
    raise ValueError("API_ID, API_HASH, and BOT_TOKEN must be set.")

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(name)

# Создаем клиент
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Список администраторов
admins = set()


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    admins.add(user_id)
    logger.info(f'Пользователь {user_id} добавлен в администраторы.')
    welcome_message = (
        f'Привет, {event.sender.first_name}! Вы добавлены как администратор.\n\n'
        'Вот несколько команд, которые вы можете использовать:\n'
        '/delete @<ник-пользователя> - Удалить пользователя из чата.'
    )
    await event.respond(welcome_message)


@client.on(events.NewMessage(pattern='/delete (.+)'))
async def delete(event):
    user_id = event.sender_id
    logger.info(f'Пользователь {user_id} пытается удалить пользователя.')

    if user_id not in admins:
        await event.respond('У вас нет прав для выполнения этой команды.')
        logger.warning(f'Пользователь {user_id} не имеет прав для удаления.')
        return

    username = event.pattern_match.group(1).lstrip('@')

    # Удаление пользователя из текущего чата
    chat = await event.get_chat()
    try:
        # Получаем участников чата с фильтром
        participants = await client(GetParticipantsRequest(
            chat,
            filter=ChannelParticipantsSearch(''),
            offset=0,
            limit=100,
            hash=0
        ))

        # Поиск пользователя по имени
        for participant in participants.users:
            if participant.username == username:
                # Удаляем участника из чата с правами, которые его банят
                banned_rights = ChatBannedRights(
                    until_date=None,
                    view_messages=True,
                    send_messages=True,
                    send_media=True,
                    send_stickers=True,
                    send_gifs=True,
                    send_games=True,
                    send_inline=True,
                    embed_links=True,
                    send_polls=True
                )
                await client(EditBannedRequest(chat, participant, banned_rights))
                chat_title = chat.title if hasattr(chat, 'title') else 'Этот чат'
                await event.respond(f'Пользователь {username} удален из чата {chat_title}.')
                return

        chat_title = chat.title if hasattr(chat, 'title') else 'Этот чат'
        await event.respond(f'Пользователь {username} не найден в чате {chat_title}.')

    except Exception as e:
        logger.warning(f'Не удалось удалить пользователя {username} из чата: {e}')
        await event.respond(f'Произошла ошибка: {e}')


# Запуск клиента
if name == 'main':
    client.run_until_disconnected()
