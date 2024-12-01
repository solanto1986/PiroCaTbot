import logging
import os
from dotenv import load_dotenv  # Для загрузки переменных окружения из .env файла
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import PeerChannel

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем данные из переменных окружения
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Проверка значений
if not API_ID or not API_HASH or not BOT_TOKEN:
    raise ValueError("API_ID, API_HASH, and BOT_TOKEN must be set.")

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем клиент
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Список администраторов
admins = set()

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    admins.add(user_id)
    welcome_message = (
        f'Привет, {event.sender.first_name}! Вы добавлены как администратор.\n\n'
        'Вот несколько команд, которые вы можете использовать:\n'
        '/delete @<ник-пользователя> - Удалить пользователя из всех чатов.\n'
        'Если у вас есть вопросы, просто напишите мне!'
    )
    await event.respond(welcome_message)

@client.on(events.NewMessage(pattern='/delete (.+)'))
async def delete(event):
    if event.sender_id not in admins:
        await event.respond('У вас нет прав для выполнения этой команды.')
        return

    username = event.pattern_match.group(1).lstrip('@')

    # Удаление пользователя из всех чатов
    async for dialog in client.iter_dialogs():
        chat = dialog.entity
        if isinstance(chat, PeerChannel):
            try:
                participants = await client(GetParticipantRequest(chat, filter=None))
                for participant in participants:
                    if participant.username == username:
                        await client.kick_participant(chat, participant)
                        await event.respond(f'Пользователь {username} удален из чата {chat.title}.')
                        break
                else:
                    await event.respond(f'Пользователь {username} не найден в чате {chat.title}.')
            except Exception as e:
                logger.warning(f'Не удалось удалить пользователя {username} из чата {chat.title}: {e}')

# Запуск клиента
if __name__ == '__main__':
    client.run_until_disconnected()
