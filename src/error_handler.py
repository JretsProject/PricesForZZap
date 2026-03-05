# src/error_handler.py

import traceback
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# Папка для сохранения файлов с критическими ошибками
CRITICAL_ERRORS_DIR = Path("logs") / "critical_errors"

def _ensure_error_dir():
    """Создаёт папку для критических ошибок, если её нет."""
    CRITICAL_ERRORS_DIR.mkdir(parents=True, exist_ok=True)

def log_critical_error(exception: Exception, context: dict = None) -> Path:
    """
    Записывает информацию о критической ошибке в JSON-файл с меткой времени.

    Args:
        exception: Объект исключения.
        context: Дополнительный словарь с контекстом (например, имя файла, параметры).

    Returns:
        Path: Путь к созданному файлу с ошибкой.
    """
    _ensure_error_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = CRITICAL_ERRORS_DIR / f"error_{timestamp}.json"

    error_data = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "traceback": traceback.format_exc(),
        "context": context or {}
    }

    try:
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        logger.error(f"Критическая ошибка записана в {error_file}")
        return error_file
    except Exception as e:
        logger.error(f"Не удалось записать критическую ошибку в файл: {e}")
        # В случае ошибки записи возвращаем None, но лучше пробросить дальше?
        # Оставим так, чтобы не прерывать основной поток.
        return None