# Fastapi-test-task

# Wallet Service API

## Overview
RESTful API service for managing digital wallets with support for deposits and withdrawals.

## Features
- Async PostgreSQL with connection pooling
- Concurrent transaction safety with row-level locking
- Automatic retry mechanism
- Transaction monitoring and logging
- Database migrations with Liquibase
- Comprehensive test coverage with async testing
- Decimal precision for financial operations
- Input validation and error handling

## Technical Details
- FastAPI framework for high performance
- SQLAlchemy with async support and row-level locking
- PgBouncer for connection pooling in transaction mode
- Pydantic for data validation
- Liquibase for database versioning
- PostgreSQL for ACID compliance
- Docker for containerization
- pytest-asyncio for async testing

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
# Run all tests with coverage
docker-compose exec app pytest tests/ -v --cov=app --cov-report=term-missing
# Run specific test file
docker-compose exec app pytest tests/test_wallets.py -v
# Run tests with specific marker
docker-compose exec app pytest -m "asyncio" tests/
```
## Test Database
Tests use a separate database with:
- Automatic creation/cleanup
- Transaction isolation
- Concurrent operation testing
- Row-level locking verification
- Connection pool stress testing

## Performance Monitoring
Monitor system performance during load tests:
- Database connections: `SELECT count(*) FROM pg_stat_activity;`
- Connection pools: Check pool usage in application logs
- System resources: Use `htop` or similar tools
- Response times: Monitor through Locust UI
- Transaction duration: Check application logs

## API Documentation
Available at http://localhost:8000/docs

## Error Handling
- 400 - Bad Request (e.g., insufficient funds)
- 404 - Wallet not found
- 422 - Validation error (e.g., negative amount)

All other errors return 200 OK with operation status "FAILED" and details in the response body.

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
-- Transaction status
SHOW TOTALS;
```

## Connection Pooling
The service uses PgBouncer for connection pooling with:
- Transaction pooling mode
- Dynamic user authentication
- Connection limits and timeouts
- Monitoring capabilities
- Automatic connection cleanup

## Development
- Use `pytest.mark.asyncio` for async tests
- Implement proper cleanup in test fixtures
- Use row-level locking for concurrent operations
- Monitor transaction duration
- Handle database connection errors gracefully