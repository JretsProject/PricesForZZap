"""
Модуль для обработки Excel-файла: очистка производителя и обновление наименования.
"""

import re
from pathlib import Path
from typing import Optional
import shutil
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


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Очищает DataFrame, содержащий колонки 'Производитель', 'Наименование' и 'Код товара':
    - Удаляет полностью пустые строки.
    - Применяет clean_manufacturer к производителю.
    - Заменяет пустые значения на "НЕ ОПРЕДЕЛЕН".
    - Добавляет производителя в наименование (в формате "Наименование [Производитель]").
    - Возвращает очищенный DataFrame.
    Логирует количество удалённых строк и установленных "НЕ ОПРЕДЕЛЕН".
    """
    # Проверка наличия обязательных колонок
    required_columns = ["Наименование", "Производитель", "Код товара"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"В DataFrame отсутствует столбец '{col}'")

    # Копируем, чтобы не изменять исходный
    df = df.copy()

    # Удаление полностью пустых строк
    before = len(df)
    df.dropna(how='all', inplace=True)
    after = len(df)
    empty_rows_removed = before - after
    if empty_rows_removed > 0:
        logger.info(f"Удалено полностью пустых строк: {empty_rows_removed}")

    undefined_set = 0  # счётчик для логирования

    # Обрабатываем каждую строку
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
            manufacturer_clean = df.at[idx, "Производитель"]
            if manufacturer_clean != "НЕ ОПРЕДЕЛЕН":
                new_name = f"{name} [{manufacturer_clean}]"
            else:
                new_name = name
            df.at[idx, "Наименование"] = new_name

    logger.info(f"Пропусков заполнено 'НЕ ОПРЕДЕЛЕН': {undefined_set}")
    return df



def process_excel(file_path: Path) -> Optional[Path]:
    """
    Обрабатывает одиночный Excel-файл:
    - Читает лист "Лист_1"
    - Очищает данные через clean_dataframe
    - Сохраняет результат с суффиксом _to_be_sent
    Возвращает путь к сохранённому файлу или None при ошибке.
    """
    logger.info(f"Начало обработки файла: {file_path}")

    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return None

    try:
        df = pd.read_excel(file_path, sheet_name="Лист_1", header=0, dtype=str)
        logger.info(f"Загружено строк: {len(df)}")
    except Exception as e:
        logger.error(f"Ошибка чтения Excel: {e}")
        return None

    try:
        df = clean_dataframe(df)
    except ValueError as e:
        logger.error(f"Ошибка очистки данных: {e}")
        return None

    # Упорядочивание колонок
    df = df[['Производитель', 'Код товара', 'Наименование', 'Кол-во', 'Цена']]

    # Формирование имени выходного файла
    output_filename = file_path.stem + "_to_be_sent" + file_path.suffix
    output_path = file_path.parent / output_filename

    try:
        df.to_excel(output_path, sheet_name="Лист_1", index=False)
        logger.success(f"Файл успешно сохранён: {output_path}")
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


def process_sales_with_purchase(sales_path: Path, purchase_path: Path) -> bool:
    """
    Обрабатывает пару файлов: продажи и закупки.
    - Загружает оба файла.
    - Сопоставляет по колонке "Код".
    - Если поставщик из purchase == "АвтоЗапчасть КАМАЗ", заменяет производителя в sales на "ПАО КАМАЗ".
    - Добавляет колонку "ЦенаЗакупки" из purchase.
    - Вызывает clean_dataframe для sales.
    - Сохраняет два файла:
        * основной: без колонки "ЦенаЗакупки" (с суффиксом _to_be_sent)
        * дополнительный: с колонкой "ЦенаЗакупки" (с суффиксом _with_purchase)
    - Архивирует исходные файлы.
    Возвращает True при успехе, иначе False.
    """
    logger.info(f"Обработка пары: продажи={sales_path.name}, закупки={purchase_path.name}")

    # Проверка существования
    if not sales_path.exists() or not purchase_path.exists():
        logger.error("Один из файлов не существует")
        return False

    try:
        sales_df = pd.read_excel(sales_path, sheet_name="Лист_1", header=0, dtype=str)
        purchase_df = pd.read_excel(purchase_path, sheet_name="Лист_1", header=0, dtype=str)
        logger.info(f"Загружено: продажи {len(sales_df)} строк, закупки {len(purchase_df)} строк")
        
        # --- ВСТАВИТЬ ЭТОТ БЛОК ---
        # Переименование колонок в файле закупок для соответствия ожидаемым
        rename_purchase = {}
        if 'Итого' in purchase_df.columns:
            rename_purchase['Итого'] = 'Кол-во'
        if 'Unnamed: 7' in purchase_df.columns:
            rename_purchase['Unnamed: 7'] = 'Цена'
        if rename_purchase:
            purchase_df.rename(columns=rename_purchase, inplace=True)
            logger.info(f"Переименованы колонки в файле закупок: {rename_purchase}")
        # -------------------------

        # ВРЕМЕННО: выводим реальные названия колонок для проверки
        logger.info(f"Колонки в файле продаж: {list(sales_df.columns)}")
        logger.info(f"Колонки в файле закупок после переименования: {list(purchase_df.columns)}")
    except Exception as e:
        logger.exception(f"Ошибка загрузки: {e}")
        return False

    # Проверка наличия обязательных колонок
    required_sales = ["Код", "Производитель", "Наименование", "Кол-во", "Цена"]
    required_purchase = ["Код", "Поставщик", "Цена"]
    for col in required_sales:
        if col not in sales_df.columns:
            logger.error(f"В файле продаж отсутствует колонка '{col}'")
            return False
    for col in required_purchase:
        if col not in purchase_df.columns:
            logger.error(f"В файле закупок отсутствует колонка '{col}'")
            return False

    # Приводим код к строке и убираем лишние пробелы
    sales_df["Код"] = sales_df["Код"].astype(str).str.strip()
    purchase_df["Код"] = purchase_df["Код"].astype(str).str.strip()

    # Создаём словарь из purchase: {код: (поставщик, цена)}
        # Приводим код к строке и убираем лишние пробелы (если ещё не сделано)
    # (эта часть уже есть выше, но для надёжности можно повторить)
    sales_df["Код"] = sales_df["Код"].astype(str).str.strip()
    purchase_df["Код"] = purchase_df["Код"].astype(str).str.strip()

    # Создаём словарь из purchase: {код: (поставщик, цена)}
    purchase_dict = {}
    for _, row in purchase_df.iterrows():
        code = row["Код"]
        if code == "nan" or code == "":  # пропускаем невалидные коды
            continue
        supplier = row.get("Поставщик")
        price = row.get("Цена")
        # Обрабатываем пропуски
        supplier = "" if pd.isna(supplier) else str(supplier).strip()
        price = "" if pd.isna(price) else str(price).strip()
        purchase_dict[code] = (supplier, price)

    # Добавляем колонку "ЦенаЗакупки" в sales, заполняем пустой строкой
    sales_df["ЦенаЗакупки"] = ""

    # Проходим по строкам sales и обновляем
    for idx, row in sales_df.iterrows():
        code = row["Код"]
        if code in purchase_dict:
            supplier, price = purchase_dict[code]
            # Замена производителя
            if supplier.lower() == "автозапчасть камаз":  # уже строка, приведена к нижнему регистру
                sales_df.at[idx, "Производитель"] = "ПАО КАМАЗ"
                logger.debug(f"Код {code}: производитель заменён на ПАО КАМАЗ")
            # Добавление цены закупки
            sales_df.at[idx, "ЦенаЗакупки"] = price
        else:
            logger.debug(f"Код {code} не найден в закупках, цена закупки не добавлена")

    # Переименовываем "Код" в "Код товара" для clean_dataframe
    #sales_df.rename(columns={"Код": "Код товара"}, inplace=True)

    # Проверяем наличие всех колонок, необходимых для clean_dataframe
    # clean_dataframe ожидает "Наименование", "Производитель", "Код товара"
    try:
        sales_df = clean_dataframe(sales_df)
    except ValueError as e:
        logger.error(f"Ошибка clean_dataframe: {e}")
        return False

    # Упорядочивание колонок для выходного файла (как в process_excel)
    base_columns = ['Производитель', 'Код товара', 'Наименование', 'Кол-во', 'Цена']
    # Убедимся, что все колонки присутствуют
    for col in base_columns:
        if col not in sales_df.columns:
            logger.error(f"После очистки отсутствует колонка '{col}'")
            return False

    # Сохраняем два файла
    # 1. Основной (без ЦенаЗакупки)
    main_df = sales_df[base_columns].copy()
    main_output = sales_path.parent / f"{sales_path.stem}_to_be_sent{sales_path.suffix}"
    try:
        main_df.to_excel(main_output, sheet_name="Лист_1", index=False)
        logger.success(f"Основной файл сохранён: {main_output}")
    except Exception as e:
        logger.error(f"Ошибка сохранения основного файла: {e}")
        return False

    # 2. Дополнительный (с ЦенаЗакупки)
    # Добавляем колонку ЦенаЗакупки, если она есть
    if "ЦенаЗакупки" in sales_df.columns:
        extra_columns = base_columns + ['Код', 'ЦенаЗакупки']
        extra_df = sales_df[extra_columns].copy()
        extra_output = sales_path.parent / f"{sales_path.stem}_with_purchase{sales_path.suffix}"
        try:
            extra_df.to_excel(extra_output, sheet_name="Лист_1", index=False)
            logger.success(f"Дополнительный файл сохранён: {extra_output}")
        except Exception as e:
            logger.error(f"Ошибка сохранения дополнительного файла: {e}")
            # Не прерываем выполнение, основной файл уже сохранён

    # Архивирование исходных файлов
    try:
        archive_original(sales_path)
        archive_original(purchase_path)
        logger.info("Исходные файлы заархивированы")
    except Exception as e:
        logger.error(f"Ошибка при архивации: {e}")
        # Не прерываем, так как обработка уже выполнена

    return True