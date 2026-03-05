# tests/test_find_file.py

import sys
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

# Загружаем переменные окружения из корневого .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Добавляем корень проекта в путь для импорта модулей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import find_file_by_pattern
from src.error_handler import log_critical_error
from config.settings import WATCH_FOLDER, PURCHASE_PATTERN_ZZAP, SALES_PATTERN_ZZAP

def test_real_files():
    """Проверяет поиск реальных файлов в рабочей папке за сегодняшнюю дату."""
    print("=== ТЕСТИРОВАНИЕ НА РЕАЛЬНЫХ ФАЙЛАХ ===\n")

    # Целевая дата (можно изменить на нужную вручную)
    target_date = date.today().isoformat()  # '2026-03-05'
    print(f"Ищем файлы за {target_date} в папке: {WATCH_FOLDER}")

    watch_path = Path(WATCH_FOLDER)
    if not watch_path.exists():
        print(f"❌ Папка {WATCH_FOLDER} не существует.")
        return

    # Поиск файла закупок
    print("\n--- Поиск файла закупок ---")
    try:
        purchase_file = find_file_by_pattern(
            folder=watch_path,
            pattern=PURCHASE_PATTERN_ZZAP,
            date_str=target_date,
            multiple=False
        )
        print(f"✅ Найден: {purchase_file.name}")
        print(f"   Полный путь: {purchase_file}")
    except FileNotFoundError:
        print(f"❌ Файл закупок за {target_date} не найден.")
    except ValueError as e:
        print(f"❌ Ошибка: найдено несколько файлов закупок:\n{e}")

    # Поиск файла продаж
    print("\n--- Поиск файла продаж ---")
    try:
        sales_file = find_file_by_pattern(
            folder=watch_path,
            pattern=SALES_PATTERN_ZZAP,
            date_str=target_date,
            multiple=False
        )
        print(f"✅ Найден: {sales_file.name}")
        print(f"   Полный путь: {sales_file}")
    except FileNotFoundError:
        print(f"❌ Файл продаж за {target_date} не найден.")
    except ValueError as e:
        print(f"❌ Ошибка: найдено несколько файлов продаж:\n{e}")

    # Тестирование записи критической ошибки (опционально)
    print("\n--- Тестирование логирования ошибки ---")
    try:
        # Искусственно вызываем исключение, чтобы проверить запись в файл
        raise RuntimeError("Тестовая ошибка для проверки error_handler")
    except Exception as e:
        context = {"test": "test_find_file.py", "date": target_date}
        error_file = log_critical_error(e, context)
        if error_file and error_file.exists():
            print(f"✅ Файл ошибки создан: {error_file}")
        else:
            print("❌ Не удалось создать файл ошибки.")

if __name__ == "__main__":
    test_real_files()