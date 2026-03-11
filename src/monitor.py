
# src/monitor.py
"""
Модуль для мониторинга появления файла и запуска обработки.
"""
from pathlib import Path
from loguru import logger
from config.settings import WATCH_FOLDER, SALES_FILE, PURCHASE_FILE
from src.registry import is_processed, mark_processed
from src.processor import process_sales_with_purchase, archive_original

def check_and_process() -> bool:
    """
    Проверяет наличие обоих файлов (продаж и закупок) в целевой папке.
    Если оба существуют и не обработаны (или изменились), запускает обработку.
    Возвращает True, если обработка была выполнена успешно, иначе False.
    """
    watch_folder = Path(WATCH_FOLDER)
    sales_path = watch_folder / SALES_FILE
    purchase_path = watch_folder / PURCHASE_FILE

    logger.info(f"Проверка наличия файлов: {SALES_FILE} и {PURCHASE_FILE} в {watch_folder}")

    # Проверяем существование обоих файлов
    if not sales_path.exists():
        logger.info(f"Файл продаж {SALES_FILE} не найден.")
        return False
    if not purchase_path.exists():
        logger.info(f"Файл закупок {PURCHASE_FILE} не найден.")
        return False

    # Получаем время последнего изменения
    sales_mtime = sales_path.stat().st_mtime
    purchase_mtime = purchase_path.stat().st_mtime

    # Проверяем, не обработаны ли файлы (по реестру)
    if is_processed(SALES_FILE, sales_mtime) and is_processed(PURCHASE_FILE, purchase_mtime):
        logger.info("Оба файла уже были обработаны с текущими временами изменений.")
        return False

    logger.info("Начинаем обработку пары файлов.")
    try:
        result = process_sales_with_purchase(sales_path, purchase_path)
        if result:
            # Помечаем оба файла как обработанные
            mark_processed(SALES_FILE, sales_mtime, metadata={"type": "sales"})
            mark_processed(PURCHASE_FILE, purchase_mtime, metadata={"type": "purchase"})
            logger.info("Обработка успешно завершена, файлы помечены в реестре.")
            return True
        else:
            logger.error("Обработка не удалась (функция вернула False).")
            return False
    except Exception as e:
        logger.exception(f"Критическая ошибка при обработке: {e}")
        return False