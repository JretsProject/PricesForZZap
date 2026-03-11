# src/utils.py

import re
from pathlib import Path
from typing import Union, List, Optional, Callable
from loguru import logger

def find_file_by_pattern(
    folder: Union[str, Path],
    pattern: str,
    date_str: Optional[str] = None,
    multiple: bool = False,
    filter_func: Optional[Callable[[Path], bool]] = None
) -> Union[Path, List[Path]]:
    """
    Ищет файлы в указанной папке по glob-паттерну с возможностью фильтрации по дате и пользовательской функцией.

    Args:
        folder: Путь к папке для поиска.
        pattern: Glob-паттерн (например, "*.xlsx", "*_purchase_*.xlsx").
        date_str: Строка с датой в формате YYYY-MM-DD. Если указана, дополнительно фильтрует файлы,
                  оставляя только те, у которых в имени содержится подстрока f"-{date_str}.xlsx".
        multiple: Если True, возвращает список всех найденных файлов (может быть пустым).
                  Если False, возвращает один Path. В этом случае:
                    - Если файл не найден, выбрасывается FileNotFoundError.
                    - Если найдено несколько файлов, выбрасывается ValueError.
        filter_func: Дополнительная пользовательская функция фильтрации, которая принимает Path и возвращает bool.
                     Применяется после фильтрации по дате (если она есть).

    Returns:
        Path или список Path в зависимости от параметра multiple.

    Raises:
        FileNotFoundError: Если multiple=False и ни один файл не найден.
        ValueError: Если multiple=False и найдено более одного файла.
    """
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"Папка {folder} не существует")

    # Ищем все файлы по glob-паттерну
    all_files = list(folder.glob(pattern))
    logger.debug(f"Найдено файлов по паттерну '{pattern}': {len(all_files)}")

    # Фильтрация по дате, если задана
    if date_str:
        # Ожидаем, что дата в имени стоит перед расширением и отделена дефисом
        date_pattern = re.compile(rf"-{re.escape(date_str)}\.xlsx$")
        filtered = [f for f in all_files if date_pattern.search(str(f.name))]
        logger.debug(f"После фильтрации по дате '{date_str}': {len(filtered)}")
    else:
        filtered = all_files

    # Применяем пользовательский фильтр, если передан
    if filter_func is not None:
        filtered = [f for f in filtered if filter_func(f)]
        logger.debug(f"После пользовательского фильтра: {len(filtered)}")

    if not multiple:
        # Режим одного файла
        if not filtered:
            raise FileNotFoundError(
                f"Не найден файл по паттерну '{pattern}'"
                + (f" с датой {date_str}" if date_str else "")
                + f" в папке {folder}"
            )
        if len(filtered) > 1:
            raise ValueError(
                f"Найдено несколько файлов ({len(filtered)}) по заданным критериям в папке {folder}:\n"
                + "\n".join(str(f) for f in filtered)
            )
        logger.info(f"Найден файл: {filtered[0].name}")
        return filtered[0]
    else:
        # Режим множественного выбора: возвращаем список (может быть пустым)
        logger.info(f"Найдено файлов: {len(filtered)}")
        return filtered