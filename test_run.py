# test_run.py
from pathlib import Path
from src.processor import process_excel, archive_original
from config.settings import ARCHIVE_FOLDER
import sys
from loguru import logger

# Настройка логгера для вывода в консоль
logger.remove()
logger.add(sys.stderr, level="INFO")

# Путь к тестовому файлу
test_file = Path("data/test_kamaz.xlsx")

if not test_file.exists():
    logger.error(f"Тестовый файл не найден: {test_file}")
    sys.exit(1)

# Запуск обработки
result = process_excel(test_file)

if result:
    logger.info(f"Обработка завершена, результат: {result}")
    # Попробуем заархивировать оригинал (если папка архива существует)
    if ARCHIVE_FOLDER.exists():
        archive_original(test_file)
    else:
        logger.warning(f"Папка архива {ARCHIVE_FOLDER} не существует, пропускаем архивацию.")
else:
    logger.error("Обработка не удалась.")