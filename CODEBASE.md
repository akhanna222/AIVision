# AIVision Codebase Summary

Document OCR extraction service using multiple LLM vision models (Gemini, GPT-4o, Claude) with template-based field extraction.

## Architecture

```
User → Nginx (port 3000) → React Frontend
                        → FastAPI Backend (port 8000) → PostgreSQL
                                                     → Vision APIs (Gemini/OpenAI/Anthropic)
```

## Feature-Based Code Hierarchy

```
app/
├── api/v1/                    # REST Endpoints
│   ├── extractions.py         # POST /extract - Main document processing
│   ├── templates.py           # Template CRUD for extraction rules
│   ├── accounts.py            # Account/API key management
│   ├── categories.py          # Document category management
│   ├── tags.py                # Document tagging
│   ├── webhooks.py            # Event notifications
│   ├── analytics.py           # Usage statistics
│   ├── countries.py           # Country-specific templates
│   └── logs.py                # API request logging
│
├── core/                      # Business Logic
│   ├── extractor.py           # Orchestrates extraction flow
│   ├── multi_model_extractor.py  # LLM fallback chain
│   ├── document_classifier.py # Auto-detect document type
│   ├── pricing.py             # Cost calculation per model
│   └── quality_scorer.py      # Extraction confidence scoring
│
├── services/                  # External Integrations
│   ├── vision/
│   │   ├── gemini_client.py   # Google Gemini API
│   │   ├── openai_client.py   # OpenAI GPT-4o API
│   │   └── anthropic_client.py # Claude API
│   └── pdf_processor.py       # PDF to image conversion
│
├── db/                        # Data Layer
│   ├── models.py              # SQLAlchemy models
│   ├── crud.py                # Database operations
│   └── session.py             # Connection management
│
├── models/                    # Pydantic Schemas
│   └── *.py                   # Request/response validation
│
├── config.py                  # Environment settings
└── main.py                    # FastAPI app entry point

frontend/src/
├── pages/                     # React Pages
│   ├── Dashboard.tsx          # Main overview
│   ├── Extraction.tsx         # Upload & extract UI
│   ├── Templates.tsx          # Template editor
│   ├── Categories.tsx         # Category management
│   ├── Tags.tsx               # Tag management
│   └── APILogs.tsx            # Request history
├── components/                # Reusable UI
├── services/api.ts            # Backend API client
└── App.tsx                    # Routing & auth
```

## Troubleshooting Guide

### 1. Service Won't Start

```bash
./scripts/manage.sh status      # Check service status
./scripts/manage.sh logs        # View logs
./scripts/manage.sh kill-ports  # Port conflicts
./scripts/manage.sh restart
```

**Files to check:**
- `/etc/systemd/system/aivision-backend.service`
- `/opt/aivision/.env`

### 2. Database Issues

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT 1"
cd /opt/aivision && source venv/bin/activate
alembic current
alembic upgrade head
```

**Files to check:**
- `app/db/session.py:15-30`
- `alembic/versions/`
- `.env` → `DATABASE_URL`

### 3. Extraction Failures

| Error | Check | File |
|-------|-------|------|
| "No API key" | `.env` has API keys | `app/config.py:20-40` |
| "Model not found" | Valid model name | `app/core/multi_model_extractor.py:25-50` |
| "PDF processing failed" | `poppler-utils` installed | `app/services/pdf_processor.py` |
| "Rate limited" | API quota exceeded | `app/services/vision/*.py` |

**Extraction flow:**
```
api/v1/extractions.py:extract()
  → core/extractor.py:process()
    → services/pdf_processor.py:convert()
    → core/multi_model_extractor.py:extract()
      → services/vision/gemini_client.py (or openai/anthropic)
```

### 4. Frontend Issues

```bash
cd /opt/aivision/frontend && npm run build
sudo nginx -t
sudo systemctl restart nginx
```

**Files to check:**
- `frontend/.env` → `VITE_API_URL`
- `/etc/nginx/sites-available/aivision`
- `frontend/src/services/api.ts`

### 5. Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Invalid/missing token | Check `Authorization: Bearer aiv_xxx` header |
| 403 Forbidden | Account inactive | `app/db/crud.py:get_account_by_token()` |

### 6. Log Locations

```bash
sudo journalctl -u aivision-backend -f   # Backend
sudo tail -f /var/log/nginx/error.log    # Nginx
```

### 7. Health Checks

```bash
curl http://localhost:8000/health
curl -I http://localhost:8000/docs
curl -I http://localhost:3000
```

### 8. Full Reset

```bash
./scripts/manage.sh clean
./deploy.sh
```

## Configuration

| Setting | Location | Purpose |
|---------|----------|---------|
| `DATABASE_URL` | `.env` | PostgreSQL connection |
| `GOOGLE_API_KEY` | `.env` | Gemini API (free tier) |
| `OPENAI_API_KEY` | `.env` | GPT-4o API |
| `ANTHROPIC_API_KEY` | `.env` | Claude API |
| `BACKEND_PORT` | `.env` | API server port (default: 8000) |
| `FRONTEND_PORT` | `.env` | Web UI port (default: 3000) |
| `SECRET_KEY` | `.env` | JWT signing key |
