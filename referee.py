# referee.py (версия 2)

import requests
import redis
import sys
import time
import json
import uuid

# --- НАСТРОЙКИ ---
TOKEN = '***REMOVED***'
CHAT_ID = '-1002998392121'
TOPIC_ID = 101
REDIS_HOST = '192.168.176.166'
REDIS_PORT = 6379
CHANNEL = 'relay_channel'
# --- КОНЕЦ НАСТРОЕК ---

# Для этой версии Рефери нам понадобится Telethon, чтобы читать чат
try:
    from telethon.sync import TelegramClient
    # Вставьте ВАШИ API_ID и API_HASH
    API_ID = ***REMOVED***
    API_HASH = '***REMOVED***'
except ImportError:
    print("🔴 Telethon не установлен. Пожалуйста, установите: pip install telethon")
    sys.exit(1)

def send_telegram_message(text_to_send):
    """Отправляет сообщение в нужный топик Telegram."""
    api_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': text_to_send,
        'message_thread_id': TOPIC_ID
    }
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ Ошибка Telegram API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Критическая ошибка при отправке сообщения: {e}")

def start_new_race(r_conn):
    """Организует и запускает новый раунд эстафеты."""
    referee_id = f"referee-{uuid.uuid4().hex[:6]}"
    
    # 1. Очищаем старые данные и собираем готовых участников
    r_conn.delete('processed_bots')
    r_conn.publish(CHANNEL, json.dumps({'type': 'roll_call'}))
    print(f"[{referee_id}] 📢 Отправлен клич 'roll_call'. Ждем ответы 5 секунд...")
    
    time.sleep(5)

    # 2. Собираем ответивших и формируем очередь
    ready_bots = sorted(list(r_conn.smembers('processed_bots')))
    if not ready_bots:
        print(f"[{referee_id}] 😔 Никто не ответил на клич.")
        send_telegram_message("😔 Никто из участников не готов к эстафете.")
        return
        
    print(f"[{referee_id}] 👍 Готовые участники: {ready_bots}")
    
    # 3. Объявляем порядок в чате
    announcement = "Объявляю порядок эстафеты:\n"
    for i, bot_id in enumerate(ready_bots):
        announcement += f"{i+1}. {bot_id}\n"
    send_telegram_message(announcement)
    
    # 4. Запускаем эстафету
    start_payload = {'type': 'start_race', 'order': ready_bots}
    r_conn.publish(CHANNEL, json.dumps(start_payload))
    print(f"[{referee_id}] 🚀 Эстафета запущена!")

def poll_telegram_for_start_command(client, r_conn):
    """
    Активно проверяет Telegram-чат на наличие команды "начинаю эстафету".
    Это надежнее, чем пассивное ожидание события.
    """
    print("🔍 Рефери начал проверять чат на наличие команды 'начинаю эстафету'...")
    last_message_id = 0
    # При первом запуске узнаем ID последнего сообщения, чтобы не реагировать на старые
    for msg in client.iter_messages(int(CHAT_ID), limit=1):
        last_message_id = msg.id

    while True:
        try:
            # Проверяем 5 последних сообщений
            for message in client.iter_messages(int(CHAT_ID), limit=5, min_id=last_message_id):
                if message.raw_text and message.raw_text.lower() == "начинаю эстафету":
                    print(f"✅ Найдена команда в чате! Запускаю новый раунд.")
                    send_telegram_message("🏁 Команда получена! Начинаем подготовку к эстафете...")
                    start_new_race(r_conn)
                
                # Обновляем ID, чтобы не проверять это сообщение снова
                if message.id > last_message_id:
                    last_message_id = message.id
            
            time.sleep(3) # Пауза между проверками чата
        except Exception as e:
            print(f"❌ Ошибка при проверке сообщений в Telegram: {e}")
            time.sleep(10)

def main():
    """Главная функция Рефери."""
    print("🟢 Рефери запускается...")

    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print("✅ Подключен к Redis.")
    except Exception as e:
        print(f"❌ Не удалось подключиться к Redis: {e}")
        sys.exit(1)
        
    # Подключаемся к Telegram как юзер-клиент для чтения сообщений
    with TelegramClient('referee_session', API_ID, API_HASH) as client:
        print("✅ Клиент Telethon запущен (для чтения чата).")
        poll_telegram_for_start_command(client, r)


if __name__ == "__main__":
    main()

