"""
Конфигурация обработчиков исключений FastAPI приложения.
Содержит регистрацию обработчиков для HTTP и валидационных ошибок.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("api")

def register_exception_handlers(app: FastAPI):
    """
    Регистрирует обработчики исключений для FastAPI приложения.
    Обрабатывает HTTP ошибки и ошибки валидации запросов.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP {exc.status_code} - {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
