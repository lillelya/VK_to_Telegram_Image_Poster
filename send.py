import asyncio
from telethon import TelegramClient, errors
api_id = 123456  
api_hash = 'your_api_hash'  
chats = [
    -канал-очередь,
    -основной-канал,
]
message = "message"
client = TelegramClient('session', api_id, api_hash)
async def send_messages():
    await client.start()
    for chat in chats:
        try:
            await client.send_message(chat, message)
            await asyncio.sleep(8)
        except errors.FloodWaitError as e:
            continue
        except Exception as e:
            print(f"error {chat}: {e}")
            continue
with client:
    client.loop.run_until_complete(send_messages())
