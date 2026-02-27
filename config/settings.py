import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Корневая папка проекта
BASE_DIR = Path(__file__).parent.parent

# Папка мониторинга (преобразуем строку в Path)
WATCH_FOLDER = Path(os.getenv("WATCH_FOLDER", ""))
TARGET_FILE = os.getenv("TARGET_FILE", "kamaz_kmv.xlsx")
OUTPUT_SUFFIX = os.getenv("OUTPUT_SUFFIX", "_for_zzap")

# Реестр
REGISTRY_PATH = BASE_DIR / os.getenv("REGISTRY_PATH", "data/registry.json")

# Логирование
LOG_PATH = BASE_DIR / os.getenv("LOG_PATH", "logs/app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Стоп-слова (географические названия, которые нужно удалять целиком)
STOP_WORDS = [
    "г.",
    "город",
    "область",
    "обл",
    "республика",
    "край",
    "район",
    "Болгария",
    "Россия",
    "Московск.",
    "Московская",
    "Гатчина",
    "Рославль",
    "Н-Челны",
    "Калуга",
    # Добавляйте по мере необходимости
]

# Регулярные выражения для удаления конструкций
PATTERNS = [
    r"\bг\.\s*\w+",           # г. Москва
    r"\bобл\b",                # обл
    r"\bобласть\b",            # область
    r"\bреспублика\b",         # республика
    r"\bкрай\b",               # край
    r"\bрайон\b",              # район
    r"\bМосковск\.?\s*обл\b",  # Московск. обл
    r"\b[А-Я][а-я]+\.?\s*обл\b",  # Калужская обл
    r"г\.\s*[А-Я][а-я\-]+",    # г. Город
]