"""
Модуль для работы с реестром обработанных файлов.
Реестр хранится в JSON-файле и содержит записи об обработанных файлах.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import REGISTRY_PATH


def load_registry() -> List[Dict[str, Any]]:
    """
    Загружает реестр из JSON-файла.
    Если файл не существует, возвращает пустой список.
    """
    if not REGISTRY_PATH.exists():
        return []
    try:
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Временно используем print, позже заменим на loguru
        print(f"Ошибка загрузки реестра: {e}")
        return []


def save_registry(registry: List[Dict[str, Any]]) -> None:
    """
    Сохраняет реестр в JSON-файл.
    Создаёт родительскую папку, если её нет.
    """
    # Убедимся, что папка data существует
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def is_processed(filename: str, registry: Optional[List[Dict[str, Any]]] = None) -> bool:
    """
    Проверяет, есть ли файл с указанным именем в реестре.
    Если реестр не передан, загружает его.
    """
    if registry is None:
        registry = load_registry()
    return any(entry.get("filename") == filename for entry in registry)


def mark_processed(filename: str, metadata: Optional[Dict] = None, registry: Optional[List[Dict]] = None) -> None:
    """
    Добавляет запись об обработанном файле в реестр.
    Если реестр не передан, загружает его.
    metadata — дополнительные данные (например, время изменения исходного файла)
    """
    if registry is None:
        registry = load_registry()
    # Создаём новую запись
    entry = {
        "filename": filename,
        "processed_at": datetime.now().isoformat(),
    }
    if metadata:
        entry.update(metadata)
    registry.append(entry)
    save_registry(registry)


def clear_registry() -> None:
    """
    Очищает реестр (полезно для тестирования или администрирования).
    """
    save_registry([])