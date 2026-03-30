import asyncio
import logging
import os
import requests
from telethon import TelegramClient
from telethon.tl.types import MessageService
import vk_api

# --------------------- НАСТРОЙКИ ---------------------
API_ID = ваш_айди        
API_HASH = "ваш_хэш"
BOT_TOKEN = "токен_вашего_бота"           # в целом в итоге не пригодилось
SESSION_NAME = "session"                  # имя сессии Telethon
QUEUE_CHANNEL = 'айди_канала_очереди'     # канал-очередь
TARGET_CHANNEL = -айди_канала_постинга    # канал для постинга
VK_TOKEN = "токен_вк_личный"
VK_GROUP_ID = "айди_паблика_вк"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------- ФУНКЦИЯ VK ---------------------
def send_to_vk(file_path, caption=""):
    """Постинг фото в VK через group token"""
    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()

        upload_server = vk.photos.getWallUploadServer(group_id=int(VK_GROUP_ID))
        upload_url = upload_server['upload_url']

        with open(file_path, 'rb') as f:
            response = requests.post(upload_url, files={'photo': f}).json()

        save_result = vk.photos.saveWallPhoto(
            group_id=int(VK_GROUP_ID),
            photo=response['photo'],
            server=response['server'],
            hash=response['hash']
        )

        photo = save_result[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"

        vk.wall.post(
            owner_id=-int(VK_GROUP_ID),
            from_group=1,
            message=caption,
            attachments=attachment
        )

        logger.info("VK send")
        return True

    except Exception as e:
        logger.error(f"VK error {e}")
        return False

# --------------------- ОБРАБОТКА ОЧЕРЕДИ ---------------------
async def process_queue(client: TelegramClient):
    # постим самое старое сообщение, поэтому reverse=True. False будет брать самое новое
    messages = await client.get_messages(QUEUE_CHANNEL, limit=50, reverse=True)
    
    for message in messages:
        # скипаем системные сообщения и сообщения без изображений
        if isinstance(message, MessageService) or not message.photo or "канал создан" in (message.text or "").lower():
            await message.delete()
            logger.info(f"skip system msg {message.id}")
            continue

        # обрабатываем подходящее сообщение
        local_file_path = f"temp_{message.id}.jpg"
        await client.download_media(message.photo, local_file_path)
        logger.info(f"processing msg {message.id}")

        # VK
        success_vk = send_to_vk(local_file_path, caption=message.text or "")

        # TG
        try:
            await client.send_file(TARGET_CHANNEL, local_file_path, caption=message.text or "")
            logger.info("TG send")
            success_tg = True
        except Exception as e:
            logger.error(f"TG error {e}")
            success_tg = False

        # удаляем файл
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

        # удаляем картинку из канала-очереди, если оба постинга успешны
        if success_vk and success_tg:
            await message.delete()
            logger.info(f"msg delete {message.id}")
        else:
            logger.info(f"message {message.id} keep. popytka 2")
        break

# --------------------- MAIN ---------------------
async def main():
    logger.info("start...")
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        logger.info("login")
        while True:
            try:
                await process_queue(client)
                # пауза 1 час
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"line error: {e}")
                await asyncio.sleep(3600)

# --------------------- ЗАПУСК ---------------------
if __name__ == "__main__":
    asyncio.run(main())
