# utils/logging_utils.py
import logging
import os
from pathlib import Path

# Путь к файлу лога
LOG_FILE = Path("launcher.log")

# Уровень логирования по умолчанию
LOG_LEVEL = logging.INFO

def setup_logger(name="LauncherLogger", log_file=LOG_FILE, level=LOG_LEVEL):
    """Настраивает и возвращает логгер."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Предотвращаем дублирование хендлеров при повторных вызовах
    if logger.handlers:
        return logger

    # Форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Хендлер для файла
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Хендлер для консоли (опционально)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Добавляем хендлеры к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Создаем глобальный экземпляр логгера
logger = setup_logger()

# Функции-обертки для удобства
def log_info(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)

def log_error(message):
    logger.error(message)

def log_debug(message):
    logger.debug(message)
