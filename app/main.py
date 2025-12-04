import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config.exception_handlers_cfg import register_exception_handlers
from app.config.logger_cfg import setup_logging
from app.config.main_cfg import settings
from app.config.request_logger_cfg import log_requests
from app.routers import auth, users, content_admin, content, lesson_files

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="NeuroTutor API")

# Разрешаем запросы с фронта
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middlewares
app.middleware("http")(log_requests)

# Роуты
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(content_admin.router)
app.include_router(content.router)
app.include_router(lesson_files.router)

# Обработчики ошибок
register_exception_handlers(app)

if __name__ == "__main__":
    logger.info(f"Swagger: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG_MODE
    )
