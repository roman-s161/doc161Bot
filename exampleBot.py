from telegram.ext import Application, CommandHandler
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")
try:
    import telegram
    print(f"Telegram module found at: {telegram.__file__}")
except ImportError as e:
    print(f"Error importing telegram: {e}")

# Оригинальный импорт
from telegram.ext import Application, CommandHandler

from dotenv import load_dotenv
import os
import logging
import requests
import signal
import sys
import time
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN')
OPENWEATHER_API_KEY= os.environ.get('OPENWEATHER_API_KEY')

if not TOKEN:
    raise ValueError('BOT_TOKEN не найден')

# Словарь городов и их координат
CITIES = {
    'taganrog': {'name': 'Таганрог', 'lat': 47.2362, 'lon': 38.8969},
    'matveev_kurgan': {'name': 'Матвеев-Курган', 'lat': 47.5667, 'lon': 38.8667},
    'natalyevka': {'name': 'Натальевка', 'lat': 47.1631, 'lon': 38.6531},
    'rostov': {'name': 'Ростов-на-Дону', 'lat': 47.2357, 'lon': 39.7015},
    'sochi': {'name': 'Сочи', 'lat': 43.6028, 'lon': 39.7342}
}

# Кэш для хранения данных о погоде
# Структура: {'city_key': {'data': {...}, 'timestamp': datetime, 'source': 'api'}}
WEATHER_CACHE = {}

# Время жизни кэша (в минутах)
CACHE_TTL = 30

# Счетчик API запросов
API_REQUESTS_COUNT = 0
API_REQUESTS_RESET_DATE = datetime.now()
API_REQUESTS_LIMIT = 950  # Устанавливаем лимит чуть ниже 1000 для безопасности

# Обработчик сигналов завершения
def signal_handler(sig, frame):
    """Обработчик сигналов завершения для корректного выхода"""
    logger.info("Получен сигнал завершения. Корректное завершение работы...")
    # Здесь можно добавить код очистки ресурсов, если необходимо
    sys.exit(0)

# Регистрация обработчиков сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_weather(city_key='taganrog', max_retries=3, retry_delay=2, force_refresh=False):
    """Получение данных о погоде с кэшированием и учетом лимита запросов"""
    global API_REQUESTS_COUNT, API_REQUESTS_RESET_DATE
    
    if city_key not in CITIES:
        logger.error(f"Город {city_key} не найден")
        return None
    
    city = CITIES[city_key]
    
    # Проверяем кэш, если не требуется принудительное обновление
    current_time = datetime.now()
    if not force_refresh and city_key in WEATHER_CACHE:
        cache_entry = WEATHER_CACHE[city_key]
        cache_age = current_time - cache_entry['timestamp']
        
        # Если кэш не устарел, используем его
        if cache_age < timedelta(minutes=CACHE_TTL):
            logger.info(f"Используются кэшированные данные для {city['name']} (возраст: {cache_age})")
            return cache_entry
    
    # Сброс счетчика API запросов в новом месяце
    if current_time.month != API_REQUESTS_RESET_DATE.month:
        logger.info("Сброс счетчика API запросов (новый месяц)")
        API_REQUESTS_COUNT = 0
        API_REQUESTS_RESET_DATE = current_time
    
    # Проверка лимита API запросов
    if OPENWEATHER_API_KEY and API_REQUESTS_COUNT < API_REQUESTS_LIMIT:
        lat = city['lat']
        lon = city['lon']
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Попытка запроса API #{attempt+1} для {city['name']}")
                response = requests.get(url, timeout=10)
                
                # Увеличиваем счетчик запросов
                API_REQUESTS_COUNT += 1
                logger.info(f"Использовано {API_REQUESTS_COUNT}/{API_REQUESTS_LIMIT} API запросов в этом месяце")
                
                if response.status_code == 200:
                    # Сохраняем результат в кэш
                    result = {'data': response.json(), 'city': city['name'], 'source': 'api', 'timestamp': current_time}
                    WEATHER_CACHE[city_key] = result
                    return result
                elif response.status_code == 429:  # Превышен лимит запросов
                    logger.warning(f"Превышен лимит запросов. Ожидание перед повторной попыткой.")
                    time.sleep(retry_delay * (attempt + 1))  # Экспоненциальная задержка
                else:
                    logger.warning(f"API вернул ошибку со статусом {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            except requests.exceptions.Timeout:
                logger.error(f"Превышено время ожидания запроса на попытке {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Ошибка запроса API: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
    else:
        if API_REQUESTS_COUNT >= API_REQUESTS_LIMIT:
            logger.warning(f"Достигнут месячный лимит API запросов ({API_REQUESTS_LIMIT}). Используются демо-данные.")
        elif not OPENWEATHER_API_KEY:
            logger.warning("API ключ не найден. Используются демо-данные.")
    
    # Резервные данные, если API недоступен или превышен лимит
    logger.info(f"Использование демо-данных для {city['name']}")
    mock_data = {
        'taganrog': {
            'temp': 12.3, 'feels_like': 10.8, 'humidity': 65, 
            'pressure': 1018, 'description': 'переменная облачность', 'wind_speed': 2.1
        },
        'matveev_kurgan': {
            'temp': 11.5, 'feels_like': 9.7, 'humidity': 68, 
            'pressure': 1017, 'description': 'облачно', 'wind_speed': 3.2
        },
        'natalyevka': {
            'temp': 12.8, 'feels_like': 11.2, 'humidity': 63, 
            'pressure': 1018, 'description': 'малооблачно', 'wind_speed': 1.8
        },
        'rostov': {
            'temp': 13.5, 'feels_like': 12.1, 'humidity': 60, 
            'pressure': 1016, 'description': 'ясно', 'wind_speed': 2.5
        },
        'sochi': {
            'temp': 18.2, 'feels_like': 17.5, 'humidity': 72, 
            'pressure': 1014, 'description': 'солнечно', 'wind_speed': 1.5
        }
    }
    
    mock = mock_data.get(city_key, mock_data['taganrog'])
    
    # Сохраняем мок-данные в кэш
    result = {
        'data': {
            'main': {
                'temp': mock['temp'],
                'feels_like': mock['feels_like'],
                'humidity': mock['humidity'],
                'pressure': mock['pressure']
            },
            'weather': [{'description': mock['description']}],
            'wind': {'speed': mock['wind_speed']}
        },
        'city': city['name'],
        'source': 'mock',
        'timestamp': current_time
    }
    WEATHER_CACHE[city_key] = result
    return result

async def send_weather(update, context, city_key):
    """Общая функция для отправки данных о погоде"""
    logger.info(f"Получена команда погоды для {city_key}")
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Получаю данные о погоде... ⏳"
    )
    
    # Проверяем наличие аргумента force для принудительного обновления
    force_refresh = False
    if context.args and 'force' in context.args:
        force_refresh = True
        logger.info("Запрошено принудительное обновление данных")
    
    weather_data = get_weather(city_key, force_refresh=force_refresh)
    
    if weather_data:
        data = weather_data['data']
        city = weather_data['city']
        source = weather_data['source']
        timestamp = weather_data['timestamp']
        
        main = data.get('main', {})
        weather = data.get('weather', [{}])[0]
        wind = data.get('wind', {})
        
        temp = main.get('temp')
        feels_like = main.get('feels_like')
        humidity = main.get('humidity')
        pressure = main.get('pressure')
        description = weather.get('description', 'Неизвестно')
        wind_speed = wind.get('speed', 0)
        
        source_emoji = "🌐" if source == 'api' else "🔧"
        
        # Форматируем время последнего обновления
        update_time = timestamp.strftime("%H:%M:%S")
        
        message = f"{source_emoji} Погода в городе {city}:\n\n" \
                 f"🌡 Температура: {temp}°C\n" \
                 f"🤔 Ощущается как: {feels_like}°C\n" \
                 f"💧 Влажность: {humidity}%\n" \
                 f"📈 Давление: {pressure} гПа\n" \
                 f"💨 Ветер: {wind_speed} м/с\n" \
                 f"📊 Описание: {description}\n\n" \
                 f"🕒 Обновлено: {update_time}"
        
        if source == 'mock':
            message += "\n⚠️ Демо-данные (проблемы с API ключом или превышен лимит запросов)"
    else:
        message = "❌ Не удалось получить данные о погоде."
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def start(update, context):
    """Отправка приветственного сообщения"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Привет {update.effective_user.first_name}! 🌤\n\n"
             f"Доступные команды:\n"
             f"/weather - погода в Таганроге\n"
             f"/weather_matveev - погода в Матвеев-Кургане\n"
             f"/weather_natalyevka - погода в Натальевке\n"
             f"/weather_rostov - погода в Ростове-на-Дону\n"
             f"/weather_sochi - погода в Сочи\n"
             f"/stats - статистика использования API\n\n"
             f"Добавьте 'force' к любой команде для принудительного обновления данных,\n"
             f"например: /weather force"
    )

async def stats(update, context):
    """Отправка статистики использования API"""
    days_left = 30 - datetime.now().day
    
    message = f"📊 Статистика использования API:\n\n" \
             f"🔢 Использовано запросов: {API_REQUESTS_COUNT}/{API_REQUESTS_LIMIT}\n" \
             f"📅 Сброс счетчика через: {days_left} дней\n" \
             f"⏱ Время жизни кэша: {CACHE_TTL} минут"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def weather_command(update, context):
    """Отправка информации о погоде в Таганроге"""
    await send_weather(update, context, 'taganrog')

async def weather_matveev(update, context):
    """Отправка информации о погоде в Матвеев-Кургане"""
    await send_weather(update, context, 'matveev_kurgan')

async def weather_natalyevka(update, context):
    """Отправка информации о погоде в Натальевке"""
    await send_weather(update, context, 'natalyevka')

async def weather_rostov(update, context):
    """Отправка информации о погоде в Ростове-на-Дону"""
    await send_weather(update, context, 'rostov')

async def weather_sochi(update, context):
    """Отправка информации о погоде в Сочи"""
    await send_weather(update, context, 'sochi')

async def health_check(context):
    """Периодическая проверка работоспособности"""
    logger.info("Выполняется проверка работоспособности")
    
    # Проверка доступности API без реального запроса
    if OPENWEATHER_API_KEY:
        try:
            # Используем ping или простой запрос без счетчика
            response = requests.head("https://api.openweathermap.org/", timeout=5)
            if response.status_code < 400:
                logger.info("Проверка API успешна")
            else:
                logger.warning(f"Проверка API не пройдена: статус {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при проверке работоспособности: {e}")
    else:
        logger.warning("Проверка API пропущена: отсутствует API ключ")
    
    # Сохранение статистики использования API в файл
    try:
        with open("api_stats.txt", "w") as f:
            f.write(f"Запросов использовано: {API_REQUESTS_COUNT}/{API_REQUESTS_LIMIT}\n")
            f.write(f"Дата последнего сброса: {API_REQUESTS_RESET_DATE}\n")
        logger.info("Статистика использования API сохранена в файл")
    except Exception as e:
        logger.error(f"Ошибка при сохранении статистики: {e}")

def main():
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()
    
    # Добавление обработчиков команд
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('weather', weather_command))
    app.add_handler(CommandHandler('weather_matveev', weather_matveev))
    app.add_handler(CommandHandler('weather_natalyevka', weather_natalyevka))
    app.add_handler(CommandHandler('weather_rostov', weather_rostov))
    app.add_handler(CommandHandler('weather_sochi', weather_sochi))
    app.add_handler(CommandHandler('stats', stats))
    
    # Добавление периодической проверки работоспособности
    job_queue = app.job_queue
    job_queue.run_repeating(health_check, interval=3600)  # Запуск каждый час
    
    # Загрузка сохраненной статистики, если файл существует
    try:
        if os.path.exists("api_stats.txt"):
            logger.info("Загрузка сохраненной статистики API")
            with open("api_stats.txt", "r") as f:
                lines = f.readlines()
                if lines and len(lines) >= 1:
                    count_line = lines[0].strip()
                    if "Запросов использовано:" in count_line:
                        count_str = count_line.split(":")[1].strip().split("/")[0]
                        global API_REQUESTS_COUNT
                        API_REQUESTS_COUNT = int(count_str)
                        logger.info(f"Загружено значение счетчика API: {API_REQUESTS_COUNT}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке статистики: {e}")
    
    logger.info('Бот запускается...')
    
    try:
        app.run_polling()
    except Exception as e:
        logger.error(f'Ошибка: {e}')

if __name__ == '__main__':
    main()

