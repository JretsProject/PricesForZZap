#!/usr/bin/env python
"""
Точка входа для приложения.
Запускает однократную проверку и обработку файла.
"""

import sys
from pathlib import Path
from loguru import logger

from config.settings import LOG_PATH, LOG_LEVEL
from src.monitor import check_and_process


def setup_logging():
    """Настройка логирования в файл и консоль."""
    # Удаляем стандартный обработчик loguru
    logger.remove()
    # Добавляем вывод в консоль
    logger.add(sys.stderr, level=LOG_LEVEL)
    # Добавляем вывод в файл (папка создаётся автоматически)
    logger.add(LOG_PATH, rotation="1 MB", retention="7 days", level=LOG_LEVEL)
    logger.info("Логирование настроено.")


def main():
    setup_logging()
    logger.info("Запуск проверки наличия файла.")
    try:
        processed = check_and_process()
        if processed:
            logger.info("Обработка выполнена успешно.")
        else:
            logger.info("Обработка не требовалась или не удалась.")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)
    logger.info("Завершение работы.")


if __name__ == "__main__":
    main()