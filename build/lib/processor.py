"""
Модуль для обработки Excel-файла: очистка производителя и обновление наименования.
"""

import re
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from config.settings import (
    GEO_INDICATORS,
    COUNTRIES,
    REGIONS,
    CITIES,
    PATTERNS,
    ARCHIVE_FOLDER,
)


def clean_manufacturer(text: str) -> str:
    """
    Очищает название производителя от географических пометок.
    - Удаляет стоп-слова (страны, регионы, города и указатели)
    - Удаляет конструкции, соответствующие регулярным выражениям
    - Возвращает очищенную строку (лишние пробелы убираются)
    Если после очистки строка пуста, возвращает "НЕ ОПРЕДЕЛЕН".
    """
    if not isinstance(text, str) or not text.strip():
        return "НЕ ОПРЕДЕЛЕН"

    original = text
    # Приводим к нижнему регистру для сравнения? Нет, лучше сохранить оригинальный регистр,
    # но для удаления слов будем сравнивать без учёта регистра?
    # Для простоты будем работать в исходном регистре, но списки стоп-слов заданы в разных регистрах.
    # Лучше привести и текст, и стоп-слова к нижнему регистру для сравнения.
    text_lower = text.lower()

    # Составляем множество стоп-слов в нижнем регистре для быстрого поиска
    stop_words_set = set(
        word.lower()
        for word in (GEO_INDICATORS + COUNTRIES + REGIONS + CITIES)
        if isinstance(word, str) and word.strip()
    )

    # Разбиваем на слова (по пробелам и знакам препинания?)
    # Для начала просто split() по пробелам, но потом нужно восстановить.
    # Более надёжный подход: удалять стоп-слова как целые слова с помощью re.
    # Создадим регулярку для удаления целых слов из списка.
    if stop_words_set:
        # Экранируем специальные символы (например, точки в "г.")
        escaped_words = [re.escape(word) for word in stop_words_set]
        # Сортируем по убыванию длины, чтобы сначала удалялись более длинные слова
        escaped_words.sort(key=len, reverse=True)
        pattern = r'\b(?:' + '|'.join(escaped_words) + r')\b'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Применяем регулярные выражения из PATTERNS
    for pattern in PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Удаляем скобки всех видов: квадратные, круглые, фигурные
    text = re.sub(r'[\[\]\(\)\{\}]', '', text)
    # Удаляем одиночное "г." с пробелом
    text = re.sub(r'\bг\.\s*', '', text)
    # Удаляем лишние пробелы и знаки препинания по краям
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip(' ,.;:-')

    if not text:
        logger.warning(f"Производитель после очистки стал пустым: исходный '{original}'")
        return "НЕ ОПРЕДЕЛЕН"
    return text


def process_excel(file_path: Path) -> Optional[Path]:
    """
    Основная функция обработки файла:
    - Читает Excel
    - Применяет очистку
    - Сохраняет новый файл с суффиксом _for_zzap
    Возвращает путь к сохранённому файлу или None, если произошла ошибка.
    """
    logger.info(f"Начало обработки файла: {file_path}")

    # Проверка существования файла
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return None

    try:
        # Читаем Excel, предполагаем, что заголовки в первой строке
        df = pd.read_excel(file_path, sheet_name="Лист_1", header=0)
        logger.info(f"Загружено строк: {len(df)}")
    except Exception as e:
        logger.error(f"Ошибка чтения Excel: {e}")
        return None

    # Проверяем наличие необходимых столбцов
    required_columns = ["Наименование", "Производитель"]
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"В файле отсутствует столбец '{col}'")
            return None

    # Счётчики для логирования
    empty_rows_removed = 0
    undefined_set = 0

    # Обрабатываем строки
    # Удаляем строки, полностью пустые (все значения NaN)
    before = len(df)
    df.dropna(how='all', inplace=True)
    after = len(df)
    empty_rows_removed = before - after
    if empty_rows_removed > 0:
        logger.info(f"Удалено полностью пустых строк: {empty_rows_removed}")

    # Обрабатываем столбец "Производитель" и "Наименование"
    for idx, row in df.iterrows():
        # Производитель
        manufacturer = row.get("Производитель")
        if pd.isna(manufacturer) or str(manufacturer).strip() == "":
            logger.warning(f"Строка {idx+2}: пустой производитель, установлено 'НЕ ОПРЕДЕЛЕН'")
            df.at[idx, "Производитель"] = "НЕ ОПРЕДЕЛЕН"
            undefined_set += 1
        else:
            cleaned = clean_manufacturer(str(manufacturer))
            df.at[idx, "Производитель"] = cleaned
            if cleaned == "НЕ ОПРЕДЕЛЕН" and str(manufacturer).strip() != "":
                logger.warning(f"Строка {idx+2}: производитель после очистки стал 'НЕ ОПРЕДЕЛЕН' (был '{manufacturer}')")
                undefined_set += 1

        # Наименование
        name = row.get("Наименование")
        if pd.isna(name) or str(name).strip() == "":
            logger.warning(f"Строка {idx+2}: пустое наименование, установлено 'НЕ ОПРЕДЕЛЕН'")
            df.at[idx, "Наименование"] = "НЕ ОПРЕДЕЛЕН"
            undefined_set += 1
        else:
            # Добавляем производителя в скобках, если он не пустой
            manufacturer_clean = df.at[idx, "Производитель"]
            if manufacturer_clean != "НЕ ОПРЕДЕЛЕН":
                new_name = f"{name} [{manufacturer_clean}]"
            else:
                new_name = name  # оставляем как есть
            df.at[idx, "Наименование"] = new_name

    # Формируем имя выходного файла (с суффиксом)
    output_filename = file_path.stem + "_for_zzap" + file_path.suffix
    output_path = file_path.parent / output_filename

    # Сохраняем результат
    try:
        df.to_excel(output_path, sheet_name="Лист_1", index=False)
        logger.success(f"Файл успешно сохранён: {output_path}")
        logger.info(f"Строк обработано: {len(df)}, пропусков заполнено 'НЕ ОПРЕДЕЛЕН': {undefined_set}")
        return output_path
    except Exception as e:
        logger.error(f"Ошибка сохранения файла: {e}")
        return None


def archive_original(file_path: Path) -> None:
    """
    Копирует исходный файл в архив (если папка существует) и удаляет оригинал.
    """
    if ARCHIVE_FOLDER.exists():
        try:
            # Создаём имя с датой
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            archive_name = file_path.stem + f"_{date_str}" + file_path.suffix
            archive_path = ARCHIVE_FOLDER / archive_name
            # Копируем
            import shutil
            shutil.copy2(file_path, archive_path)
            logger.info(f"Исходный файл скопирован в архив: {archive_path}")
        except Exception as e:
            logger.error(f"Не удалось скопировать файл в архив: {e}")
            # Если копирование не удалось, всё равно пытаемся удалить оригинал? По условию - удаляем в любом случае.
    else:
        logger.warning(f"Архивная папка {ARCHIVE_FOLDER} не существует. Файл не будет скопирован.")

    # Удаляем исходный файл
    try:
        file_path.unlink()
        logger.info(f"Исходный файл удалён: {file_path}")
    except Exception as e:
        logger.error(f"Не удалось удалить исходный файл: {e}")