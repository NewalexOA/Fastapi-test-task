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
- Comprehensive test coverage
- Decimal precision for financial operations
- Input validation and error handling

## Technical Details
- FastAPI framework for high performance
- SQLAlchemy with async support
- PgBouncer for connection pooling
- Pydantic for data validation
- Liquibase for database versioning
- PostgreSQL for ACID compliance
- Docker for containerization

## API Endpoints
- `POST /api/v1/wallets/` - Create new wallet
- `GET /api/v1/wallets/{wallet_id}` - Get wallet info
- `POST /api/v1/wallets/{wallet_id}/operation` - Process deposit/withdrawal

## Quick Start
1. Clone repository
2. Copy .env.example to .env
3. Run `docker-compose up -d`
4. API available at http://localhost:8000

## Testing
Run tests with coverage report:
```bash
docker-compose exec app pytest tests/ -v --cov=app --cov-report=term-missing
```

## Load Testing
Run load tests:
```bash
# Start load test with web interface
docker-compose up locust
# Access web interface at http://localhost:8089
```

Monitor performance:
- RPS (Requests per second)
- Response time percentiles
- Error rate
- Database connection pool usage

## Performance Monitoring
Monitor system performance during load tests:
- Database connections: `SELECT count(*) FROM pg_stat_activity;`
- Connection pools: Check pool usage in application logs
- System resources: Use `htop` or similar tools
- Response times: Monitor through Locust UI

## API Documentation
Available at http://localhost:8000/docs

## Error Handling
- 400 - Bad Request (e.g., insufficient funds)
- 404 - Wallet not found
- 422 - Validation error (e.g., negative amount)
- 500 - Internal server error

## PgBouncer Monitoring
Monitor connection pooling:
```sql
-- Active pools
SHOW POOLS;
-- Connection stats
SHOW STATS;
-- Server status
SHOW SERVERS;
-- Current connections
SHOW CLIENTS;
```

## Connection Pooling
The service uses PgBouncer for connection pooling with:
- Transaction pooling mode
- Dynamic user authentication
- Connection limits and timeouts
- Monitoring capabilities
