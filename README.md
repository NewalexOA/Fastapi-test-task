# Fastapi-test-task

# Wallet Service API

## Overview
RESTful API service for managing digital wallets with support for deposits and withdrawals.

## Features
- Async PostgreSQL with connection pooling
- Concurrent transaction safety
- Automatic retry mechanism
- Transaction monitoring
- Database migrations with Liquibase

## Quick Start
1. Clone repository
2. Copy .env.example to .env
3. Run `docker-compose up -d`
4. API available at http://localhost:8000

## API Documentation
Available at http://localhost:8000/docs