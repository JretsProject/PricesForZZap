"""
Модуль для мониторинга появления файла и запуска обработки.
"""

from pathlib import Path
from loguru import logger

from config.settings import WATCH_FOLDER, TARGET_FILE
from src.registry import is_processed, mark_processed
from src.processor import process_excel, archive_original


def check_and_process() -> bool:
    """
    Проверяет наличие файла TARGET_FILE в WATCH_FOLDER.
    Если файл есть и ещё не обработан (по реестру), запускает обработку.
    Возвращает True, если обработка выполнена, иначе False.
    """
    target_path = WATCH_FOLDER / TARGET_FILE
    logger.info(f"Проверка файла: {target_path}")

    if not target_path.exists():
        logger.info(f"Файл {TARGET_FILE} не найден.")
        return False

    # Проверяем по реестру (только по имени файла, так как путь может меняться)
    if is_processed(TARGET_FILE):
        logger.info(f"Файл {TARGET_FILE} уже был обработан ранее (по реестру).")
        return False

    # Запускаем обработку
    logger.info(f"Найден новый файл {TARGET_FILE}. Начинаем обработку...")
    result_path = process_excel(target_path)

    if result_path:
        # Помечаем в реестре как обработанный
        # Можно добавить метаданные, например, время обработки (оно уже добавляется в mark_processed)
        mark_processed(TARGET_FILE, metadata={"source_path": str(target_path)})
        logger.success(f"Файл {TARGET_FILE} успешно обработан. Результат: {result_path}")

        # Архивация и удаление оригинала (функция archive_original сама решает, копировать или нет)
        archive_original(target_path)
        return True
    else:
        logger.error(f"Обработка файла {TARGET_FILE} не удалась.")
        return False