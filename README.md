# AIVision OCR Service

Document extraction service using multi-LLM vision models (Gemini, GPT-4o, Claude).

## Features

- **Multi-LLM Support**: Gemini, GPT-4o, Claude with automatic fallback
- **Template-Based Extraction**: Custom templates for any document type
- **Multi-Tenant**: Per-account data isolation
- **Auto-Classification**: Detects document type and country
- **Quality Scoring**: Confidence scores and A-F grading

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (for frontend)
- At least one API key: Gemini (free), OpenAI, or Anthropic

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd AIVision
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys and database credentials

# Setup database
alembic upgrade head

# Run backend
uvicorn app.main:app --reload

# Run frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### Docker

```bash
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

Services: Backend (8000), Frontend (3000), API docs (/docs)

## API Usage

```bash
# Create account
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "test@example.com"}'

# Extract document (use token from response above)
curl -X POST http://localhost:8000/api/v1/extractions/extract \
  -H "Authorization: Bearer aiv_your_token" \
  -F "file=@document.pdf" \
  -F "vision_model=gemini-2.0-flash-exp" \
  -F "auto_detect=true"
```

## Configuration

Key environment variables (`.env`):

```bash
DATABASE_URL=postgresql://user:pass@localhost/aivision
GEMINI_API_KEY=your_key      # Free tier available
OPENAI_API_KEY=your_key      # Optional
ANTHROPIC_API_KEY=your_key   # Optional
SECRET_KEY=random_string
```

## Project Structure

```
app/
  api/v1/          # FastAPI routes
  core/            # Business logic
  db/              # Database models and CRUD
  models/          # Pydantic schemas
  services/        # Vision clients, PDF processor
frontend/          # React + TypeScript UI
```

## EC2 Deployment (One Command)

```bash
# On a fresh Ubuntu EC2 instance:
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Prompt for API keys (Gemini, OpenAI, Anthropic)
- Install all dependencies (Python, Node.js, PostgreSQL, Nginx)
- Configure the database
- Build and deploy the application
- Create systemd services for auto-restart

See `AWS_EC2_DEPLOYMENT.md` for manual deployment steps.

## License

MIT
