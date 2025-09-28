import asyncio
import sys
from telethon import TelegramClient, events
import config  # Ваш config.py с API_ID, API_HASH, REDIS_URL, CHANNEL, BOT_LIST, RELAY_DELAY, CHANNEL_ID

if len(sys.argv) != 2:
    print("Usage: python bot_debug.py BOT_ID")
    sys.exit(1)

BOT_ID = sys.argv[1]
if BOT_ID not in config.BOT_LIST:
    print(f"Error: BOT_ID должен быть одним из {config.BOT_LIST}")
    sys.exit(1)

client = TelegramClient(f'debug_session_{BOT_ID}', config.API_ID, config.API_HASH)

async def main():
    await client.start()
    print(f"{BOT_ID}: Юзербот запущен. Жду сообщений...")

    # Слушаем ВСЕ сообщения без фильтров
    @client.on(events.NewMessage())
    async def handler(event):
        chat = await event.get_chat()
        chat_name = chat.title if hasattr(chat, 'title') else str(chat.id)
        print(f"[{BOT_ID}] Получено сообщение из чата '{chat_name}' (id={event.chat_id}): {event.raw_text}")

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
