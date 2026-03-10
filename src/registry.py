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


def get_file_record(filename: str, registry: Optional[List[Dict]] = None) -> Optional[Dict]:
    """
    Возвращает запись о файле из реестра по имени, или None, если не найдено.
    """
    if registry is None:
        registry = load_registry()
    for entry in registry:
        if entry.get("filename") == filename:
            return entry
    return None

def is_processed(filename: str, mtime: float = None, registry: Optional[List[Dict]] = None) -> bool:
    """
    Проверяет, обработан ли файл.
    Если передан mtime, сравнивает его с сохранённым.
    """
    record = get_file_record(filename, registry)
    if record is None:
        return False
    if mtime is None:
        return True  # если mtime не указан, считаем по имени
    saved_mtime = record.get("mtime")
    if saved_mtime is None:
        return True  # старая запись без mtime считаем обработанной
    return saved_mtime == mtime

def mark_processed(filename: str, mtime: float, metadata: Optional[Dict] = None, registry: Optional[List[Dict]] = None) -> None:
    """
    Добавляет запись об обработанном файле, включая время изменения.
    """
    if registry is None:
        registry = load_registry()
    # Удаляем старую запись, если есть (чтобы обновить mtime)
    registry = [entry for entry in registry if entry.get("filename") != filename]
    entry = {
        "filename": filename,
        "mtime": mtime,
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