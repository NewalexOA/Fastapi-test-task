FROM python:3.12-slim

WORKDIR /app

# Installation of dependencies for psycopg2 and Liquibase
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    default-jre \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation of Liquibase
RUN wget -O /usr/local/bin/liquibase.tar.gz https://github.com/liquibase/liquibase/releases/download/v4.25.1/liquibase-4.25.1.tar.gz \
    && cd /usr/local/bin \
    && tar -xf liquibase.tar.gz \
    && rm liquibase.tar.gz \
    && chmod +x /usr/local/bin/liquibase

# Copying requirements.txt separately for caching the layer with dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying the application code and entrypoint
COPY . .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Creating a non-privileged user and giving him rights
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/.pytest_cache && \
    chown -R appuser:appuser /app/.pytest_cache && \
    chmod 777 /tmp

USER appuser

# Adding PYTHONPATH
ENV PYTHONPATH=/app

CMD ["./entrypoint.sh"]

