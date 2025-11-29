import logging

import uvicorn
from fastapi import FastAPI

from app.config.exception_handlers_cfg import register_exception_handlers
from app.config.logger_cfg import setup_logging
from app.config.main_cfg import settings
from app.config.request_logger_cfg import log_requests
from app.routers import auth as auth_router, users as users_router, admin_content_router as admin_content, \
    content_public_router as content_public

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="NeuroTutor API")

# Middlewares
app.middleware("http")(log_requests)

# Роуты
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(admin_content.router)
app.include_router(content_public.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


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
