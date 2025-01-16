import requests
import logging
import schedule
import time

# Устанавливаем настройки логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VK_TOKEN = "VK_TOKEN" # API VK
VK_GROUP_ID = "VK_GROUP_ID"  # ID вашего паблика
TELEGRAM_TOKEN = "TELEGRAM_TOKEN" # API Телеграм
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"  # ID вашего канала 

# Глобальная переменная для хранения ID последнего отправленного поста
last_post_id = None

# Функция для получения постов из VK
def get_vk_posts():
    """Получение последних постов из VK с изображениями."""
    url = f'https://api.vk.com/method/wall.get?owner_id=-{VK_GROUP_ID}&count=5&access_token={VK_TOKEN}&v=5.131'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на успешный статус

        posts = response.json()['response']['items']
        return posts
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении постов из VK: {e}")
        return []

# Функция для отправки картинки в Telegram
def send_telegram_photo(photo_url):
    """Отправка картинки в Telegram."""
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto'
        params = {
            'chat_id': TELEGRAM_CHAT_ID,
            'photo': photo_url
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Проверка на успешный статус

        # Логирование ответа от Telegram API
        response_json = response.json()
        if response.status_code == 200:
            logger.info(f"Картинка успешно отправлена в Telegram: {photo_url}")
        else:
            logger.error(f"Ошибка при отправке картинки. Ответ от Telegram: {response_json}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке картинки в Telegram: {e}")

# Функция для проверки новых постов и отправки их в Telegram
def check_and_send_posts():
    """Проверка новых постов из VK и отправка картинок в Telegram."""
    global last_post_id
    posts = get_vk_posts()
    if posts:
        for post in posts:
            post_id = post['id']
            if last_post_id is None or post_id > last_post_id:
                last_post_id = post_id
                logger.info(f"Обнаружен новый пост с ID: {post_id}")

                # Проверяем наличие изображений в посте
                if 'attachments' in post:
                    for attachment in post['attachments']:
                        if attachment['type'] == 'photo':
                            photo_url = attachment['photo']['sizes'][-1]['url']
                            send_telegram_photo(photo_url)
                else:
                    logger.info("Нет картинок в посте.")
            else:
                logger.info(f"Пост с ID: {post_id} уже был отправлен.")
    else:
        logger.info("Нет новых постов для отправки.")

# Настроим регулярную проверку (например, раз в 10 минут)
schedule.every(10).minutes.do(check_and_send_posts)

# Запуск автопостинга
def run_bot():
    logger.info("Запуск бота автопостинга...")
    while True:
        schedule.run_pending()
        time.sleep(1)

# Запуск
run_bot()
