FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей для psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt отдельно для кэширования слоя с зависимостями
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем непривилегированного пользователя
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Команда запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
