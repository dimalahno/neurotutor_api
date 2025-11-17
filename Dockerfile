FROM python:3.13.0

# Указываем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы зависимостей отдельно, чтобы использовать кеширование слоёв
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

COPY /app/.env /app/.env

# Указываем команду для запуска FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]