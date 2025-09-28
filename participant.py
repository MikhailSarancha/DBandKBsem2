# participant.py

import requests
import redis
import sys
import time
import json
import uuid

# --- НАСТРОЙКИ ---
TOKEN = '${BOT_TOKEN}'
CHAT_ID = '-1002998392121'
TOPIC_ID = 101
REDIS_HOST = '${IP}'
REDIS_PORT = 6379
CHANNEL = 'relay_channel'
# --- КОНЕЦ НАСТРОЕК ---

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

def main():
    """Главная функция Участника."""
    my_id = f"bot-{uuid.uuid4().hex[:6]}"
    print(f"[{my_id}] 🟢 Участник запущен. Мой ID: {my_id}")

    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        ps = r.pubsub(ignore_subscribe_messages=True)
        ps.subscribe(CHANNEL)
        print(f"[{my_id}] ✅ Подключен к Redis.")
    except Exception as e:
        print(f"[{my_id}] ❌ Не удалось подключиться к Redis: {e}")
        sys.exit(1)

    for message in ps.listen():
        try:
            data = json.loads(message['data'])
            command_type = data.get('type')

            # 1. Отвечаем на клич Рефери
            if command_type == 'roll_call':
                # SADD атомарно добавит наш ID в набор. Безопасно для гонок.
                r.sadd('processed_bots', my_id)
                print(f"[{my_id}] 📢 Ответил на клич 'roll_call'.")
            
            # 2. Начинаем эстафету
            elif command_type == 'start_race':
                order = data.get('order', [])
                if my_id in order:
                    my_turn = order.index(my_id)
                    print(f"[{my_id}] 🚀 Эстафета началась! Мой номер: {my_turn + 1}")
                    
                    # Ждем своей очереди
                    for i, bot_id in enumerate(order):
                        if i < my_turn:
                            continue # Пропускаем тех, кто был до нас
                        
                        # Наша очередь
                        if bot_id == my_id:
                            print(f"[{my_id}] 🏃‍♂️ Мой ход!")
                            send_telegram_message(f"Принимаю эстафету, я номер {my_turn + 1} ({my_id})")
                            break # Выходим из цикла, так как свой ход сделали
                        
                        # Ждем, пока сходит предыдущий
                        time.sleep(3) 

        except (json.JSONDecodeError, TypeError):
            # Игнорируем сообщения, которые не в формате JSON
            continue

if __name__ == "__main__":
    main()
