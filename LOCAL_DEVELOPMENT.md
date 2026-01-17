# Local Development

## Requirements

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+

## Setup

```bash
# Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database
sudo -u postgres psql -c "CREATE DATABASE aivision;"
sudo -u postgres psql -c "CREATE USER aivision WITH PASSWORD 'dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;"

# Environment
cp .env.example .env
# Edit .env with database URL and API keys

# Migrations
alembic upgrade head

# Run backend
uvicorn app.main:app --reload --port 8000

# Run frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Docker Alternative

```bash
cp .env.example .env
# Edit .env with API keys
docker-compose up -d
```

## Testing

```bash
pytest                        # All tests
pytest --cov=app             # With coverage
pytest tests/test_api.py     # Specific file
```

## Useful Commands

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
