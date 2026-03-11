"""
Модуль для мониторинга появления файла и запуска обработки.
"""

from pathlib import Path
from loguru import logger

from config.settings import WATCH_FOLDER, TARGET_FILE
from src.registry import is_processed, mark_processed
from src.processor import process_excel, archive_original


def check_and_process() -> bool:
    target_path = WATCH_FOLDER / TARGET_FILE
    logger.info(f"Проверка файла: {target_path}")

    if not target_path.exists():
        logger.info(f"Файл {TARGET_FILE} не найден.")
        return False

    # Получаем время последнего изменения файла
    try:
        mtime = target_path.stat().st_mtime
    except Exception as e:
        logger.error(f"Не удалось получить время изменения файла: {e}")
        return False

    # Проверяем по реестру с учётом mtime
    if is_processed(TARGET_FILE, mtime):
        logger.info(f"Файл {TARGET_FILE} уже обработан (текущее время изменения совпадает с сохранённым).")
        return False

    # Запускаем обработку
    logger.info(f"Найден новый/обновлённый файл {TARGET_FILE}. Начинаем обработку...")
    result_path = process_excel(target_path)

    if result_path:
        # Помечаем в реестре как обработанный с указанием mtime
        mark_processed(TARGET_FILE, mtime, metadata={"source_path": str(target_path)})
        logger.success(f"Файл {TARGET_FILE} успешно обработан. Результат: {result_path}")

        # Архивация и удаление оригинала
        archive_original(target_path)
        return True
    else:
        logger.error(f"Обработка файла {TARGET_FILE} не удалась.")
        return False