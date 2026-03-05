import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Корневая папка проекта
BASE_DIR = Path(__file__).parent.parent

# Папка мониторинга
WATCH_FOLDER = Path(os.getenv("WATCH_FOLDER", ""))
TARGET_FILE = os.getenv("TARGET_FILE", "kamaz_kmv.xlsx")
OUTPUT_SUFFIX = os.getenv("OUTPUT_SUFFIX", "_for_zzap")

# Реестр
REGISTRY_PATH = BASE_DIR / os.getenv("REGISTRY_PATH", "data/registry.json")

# Логирование
LOG_PATH = BASE_DIR / os.getenv("LOG_PATH", "logs/app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Архивная папка
ARCHIVE_FOLDER = BASE_DIR / "data/archive"

# ----- Стоп-слова, разбитые по категориям -----

# Географические указатели (части составных наименований)
GEO_INDICATORS = [
    "г.",
    "город",
    "обл",
    "область",
    "республика",
    "край",
    "район",
]

# Страны (удаляются, если встречаются как отдельные слова)
COUNTRIES = [
    "Болгария",
    "Россия",
    "Украина",
    "Беларусь",
    "Казахстан",
    "Италия",
    # Добавляйте по мере необходимости
]

# Регионы/области
REGIONS = [
    "Московская",
    "Московск.",
    "Ленинградская",
    "Калужская",
    # Добавляйте по мере необходимости
]

# Города (основной список загружается из файла, плюс ручное дополнение)
CITIES = []
EXTRA_CITIES = [
    "Королев",
    "Н-Челны",
    "Н-челны",
    "Н-Челны",
    "Гродно",
    "Наб Челны",
    "Московск",
    "Борисов",
    "Камида",
    # Если каких-то городов нет в JSON, можно добавить вручную, например:
    # "Гатчина", "Рославль", "Н-Челны", "Набережные Челны"
]

# Загружаем города из JSON-файла, если он существует
cities_json_path = BASE_DIR / "data" / "russian-cities.json"
if cities_json_path.exists():
    try:
        with open(cities_json_path, 'r', encoding='utf-8') as f:
            cities_data = json.load(f)
            # В файле массив объектов с полем "name" (название города)
            # Извлекаем все названия городов
            CITIES = [city["name"] for city in cities_data if "name" in city]
            print(f"Загружено {len(CITIES)} городов из JSON")
    except Exception as e:
        print(f"Ошибка загрузки городов из JSON: {e}")
        CITIES = []
else:
    print(f"Файл с городами не найден: {cities_json_path}")

# Добавляем ручной список
CITIES.extend(EXTRA_CITIES)
# Убираем дубликаты
CITIES = list(set(CITIES))

# Общий список стоп-слов (для быстрой проверки)
STOP_WORDS = list(set(GEO_INDICATORS + COUNTRIES + REGIONS + CITIES))

# Регулярные выражения для удаления конструкций
PATTERNS = [
    r"\bг\.\s*\w+",                     # г. Москва
    r"\bобл\b",                          # обл
    r"\bобласть\b",                      # область
    r"\bреспублика\b",                   # республика
    r"\bкрай\b",                         # край
    r"\bрайон\b",                        # район
    r"\bМосковск\.?\s*обл\b",            # Московск. обл
    r"\b[А-Я][а-я]+\.?\s*обл\b",         # Калужская обл
    r"г\.\s*[А-Я][а-я\-]+",              # г. Город
]

# Паттерны для поиска файлов (используются в модуле контроля цен)
PURCHASE_PATTERN_ZZAP = "*_zzap_purchase_prices-*.xlsx"
SALES_PATTERN_ZZAP = "*_zzap_sales_priсes-*.xlsx"

#Параметры загрузки файлов:

