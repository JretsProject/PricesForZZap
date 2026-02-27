import os
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

# Архив
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

# Города
CITIES = [
    "Гатчина",
    "Рославль",
    "Н-Челны",
    "Набережные Челны",
    # ...
]

# Общий список стоп-слов (может пригодиться для простой фильтрации)
# Собираем из всех категорий, но исключаем указатели с точкой, если нужно
STOP_WORDS = list(set(GEO_INDICATORS + COUNTRIES + REGIONS + CITIES))
# Можно убрать "г.", если он будет обрабатываться отдельно через регулярки
# Но пока оставим как есть.

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