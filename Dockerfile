FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей для psycopg2 и Liquibase
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    default-jre \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Установка Liquibase
RUN wget -O /usr/local/bin/liquibase.tar.gz https://github.com/liquibase/liquibase/releases/download/v4.25.1/liquibase-4.25.1.tar.gz \
    && cd /usr/local/bin \
    && tar -xf liquibase.tar.gz \
    && rm liquibase.tar.gz \
    && chmod +x /usr/local/bin/liquibase

# Копируем requirements.txt отдельно для кэширования слоя с зависимостями
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения и entrypoint
COPY . .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Создаем непривилегированного пользователя и даем ему права
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/.pytest_cache && \
    chown -R appuser:appuser /app/.pytest_cache

USER appuser

# Добавляем PYTHONPATH
ENV PYTHONPATH=/app

CMD ["./entrypoint.sh"]

