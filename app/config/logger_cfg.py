"""
Модуль конфигурации системы логирования.
Настраивает базовую конфигурацию логгера с выводом в stdout.
Устанавливает уровень логирования INFO для основного логгера
и WARNING для логгера uvicorn.access.
"""

import logging
import sys

def setup_logging():
    """
    Инициализирует базовую конфигурацию системы логирования.
    Настраивает формат, уровень логирования и обработчик для вывода в stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
