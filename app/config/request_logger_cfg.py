import logging
from fastapi import Request

"""
Модуль конфигурации логирования запросов.
Предоставляет функционал для логирования входящих HTTP запросов и ответов.
"""

# Логгер для записи информации о API запросах
logger = logging.getLogger("api")

async def log_requests(request: Request, call_next):
    """
    Middleware для логирования HTTP запросов и ответов.

    Args:
        request (Request): Объект входящего HTTP запроса
        call_next: Следующий обработчик в цепочке middleware

    Returns:
        Response: Ответ от следующего обработчика
    """
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.method} {request.url}")
    return response
