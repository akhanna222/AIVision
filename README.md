# AIVision OCR Service

Enterprise-grade document extraction service powered by multi-LLM vision models (Gemini 2.0 Flash, GPT-4o, Claude Sonnet 4). Built for scale, accuracy, and flexibility.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Performance Optimization](#performance-optimization)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## Overview

AIVision is a production-ready OCR (Optical Character Recognition) service that extracts structured data from documents using state-of-the-art vision language models. Unlike traditional OCR, AIVision understands document context and can extract complex, nested information with high accuracy.

### What Makes AIVision Different

- **Multi-LLM Support**: Seamlessly switch between Gemini, GPT-4o, and Claude with automatic fallback
- **Template-Based Extraction**: Define custom extraction templates for any document type
- **Multi-Tenant SaaS Architecture**: Complete data isolation with per-account templates and settings
- **Auto-Classification**: Automatically detects document type, country, and relevant tags
- **Quality Assurance**: Built-in confidence scoring and quality grading (A-F scale)
- **JSON-Only Storage**: Extracted results stored as JSON in PostgreSQL - no file persistence
- **Webhook Notifications**: Real-time notifications with HMAC signature verification
- **Comprehensive Analytics**: Track usage, costs, model performance, and quality metrics

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Templates   │  │  Categories  │  │   Tags       │          │
│  │  Manager     │  │  Manager     │  │   Manager    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Document    │  │   Batch      │  │   API Logs   │          │
│  │  Extraction  │  │   Processor  │  │   Viewer     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS (Bearer Token Auth)
┌────────────────────────────┼────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   API Gateway + Auth                     │   │
│  │              (Bearer Token: aiv_...)                     │   │
│  └──────────────┬────────────────┬─────────────┬────────────┘   │
│                 │                │             │                 │
│  ┌──────────────▼──┐  ┌─────────▼──────┐  ┌──▼──────────────┐  │
│  │  Extraction     │  │  Template      │  │   Analytics     │  │
│  │  Service        │  │  Registry      │  │   Engine        │  │
│  └──────────────┬──┘  └────────────────┘  └─────────────────┘  │
│                 │                                                │
│  ┌──────────────▼─────────────────────────────────────────┐    │
│  │            Vision Model Orchestrator                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐  │    │
│  │  │  Gemini  │  │  OpenAI  │  │  Anthropic Claude   │  │    │
│  │  │  Client  │  │  Client  │  │       Client        │  │    │
│  │  └──────────┘  └──────────┘  └─────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   PostgreSQL Database                            │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Accounts │  │ Templates │  │Countries │  │ Extractions  │   │
│  └──────────┘  └───────────┘  └──────────┘  └──────────────┘   │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────┐   │
│  │   Tags   │  │  Webhooks │  │ APILogs  │  │  UsageLogs   │   │
│  └──────────┘  └───────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Upload**: User uploads PDF/image via React frontend
2. **Authentication**: FastAPI validates Bearer token (aiv_token)
3. **Multi-Tenant Isolation**: Request scoped to authenticated account
4. **Document Processing**:
   - PDF converted to images at 300 DPI
   - Images sent to selected vision model
5. **AI Extraction**:
   - Auto-detect document category and country
   - Apply template or use auto-detection
   - Generate 3-5 relevant tags
6. **Quality Assurance**:
   - Calculate field completeness
   - Assess confidence scores
   - Assign quality grade (A-F)
7. **Storage**:
   - JSON results stored in PostgreSQL
   - Original files DELETED (no persistence)
   - Metadata and metrics logged
8. **Webhook Notification**: Send webhook event with HMAC signature
9. **Response**: Return extraction results to frontend

---

## Key Features

### 1. Multi-LLM Vision Support

```python
# Supported models with automatic fallback
VISION_MODELS = {
    "gemini-2.0-flash-exp": GeminiClient,    # Fastest, most cost-effective
    "gpt-4o": OpenAIClient,                  # Best for complex layouts
    "claude-sonnet-4-20250514": AnthropicClient  # Best for handwriting
}
```

**Model Selection Strategy**:
- **Gemini 2.0 Flash**: Default - 95% accuracy, lowest cost ($0.00125/page)
- **GPT-4o**: Complex tables, multi-column layouts
- **Claude Sonnet 4**: Handwritten documents, poor quality scans

### 2. Template-Based Extraction

Templates define what fields to extract and how to validate them:

```json
{
  "name": "Irish Mortgage Application",
  "category": "mortgage_application",
  "country_code": "IE",
  "fields": [
    {
      "name": "applicant_full_name",
      "type": "string",
      "required": true,
      "description": "Full legal name of mortgage applicant"
    },
    {
      "name": "loan_amount",
      "type": "currency",
      "required": true,
      "validation": "positive"
    },
    {
      "name": "property_address",
      "type": "address",
      "required": true
    }
  ]
}
```

**Field Types**:
- `string`: Text fields
- `number`: Numeric values
- `currency`: Monetary amounts (auto-format)
- `date`: Date fields (ISO 8601)
- `email`: Email validation
- `phone`: Phone number extraction
- `address`: Multi-line address
- `boolean`: Yes/no fields
- `list`: Repeating items (e.g., bank transactions)

### 3. Auto-Classification & Tagging

```python
# Automatic document classification
classification = await extract_service.auto_detect_category(image_bytes, model)
# Returns: (category, confidence, country_code)
# Example: ("bank_statement", 0.95, "IE")

# Automatic tag generation
tags = await extract_service.generate_auto_tags(
    image_bytes,
    extracted_fields,
    category,
    model
)
# Returns: ["financial", "bank-of-ireland", "monthly-statement", "2024"]
```

### 4. Multi-Tenant Architecture

**Complete Data Isolation**:
- Each account has unique `aiv_` prefixed API token
- All queries filtered by `account_id`
- Templates, countries, extractions scoped to account
- Row-level security enforced in database

**Per-Account Customization**:
- Custom templates
- Custom countries
- Custom field definitions
- Custom webhooks
- Independent usage limits

### 5. Quality Assurance

**Quality Metrics**:
```python
quality_score = {
    "completeness": 0.92,  # % of required fields extracted
    "avg_confidence": 0.87,  # Average AI confidence
    "quality_grade": "B",   # A-F grade
    "fields_extracted": 12,
    "fields_required": 13,
    "low_confidence_fields": ["date_of_birth"]
}
```

**Grading Scale**:
- **A**: >90% completeness, >90% confidence
- **B**: >80% completeness, >80% confidence
- **C**: >70% completeness, >70% confidence
- **D**: >60% completeness, >60% confidence
- **F**: <60% completeness or <60% confidence

---

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework (async/await)
- **SQLAlchemy**: ORM for PostgreSQL
- **Pydantic**: Data validation and serialization
- **Alembic**: Database migrations
- **python-multipart**: File upload handling
- **PyPDF2**: PDF processing
- **Pillow**: Image manipulation
- **httpx**: Async HTTP client
- **python-jose**: JWT token handling

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool and dev server
- **TailwindCSS**: Utility-first CSS
- **React Query**: Server state management
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **React Dropzone**: File uploads
- **Lucide React**: Icon library

### Database
- **PostgreSQL 14+**: Primary database
- **JSON columns**: Store extraction results
- **Indexes**: Optimized for common queries
- **Foreign keys**: Referential integrity

### Infrastructure
- **Nginx**: Reverse proxy and static file serving
- **Gunicorn**: Python WSGI server
- **Systemd**: Service management
- **Let's Encrypt**: SSL certificates
- **AWS EC2**: Cloud deployment

---

## Database Schema

### Core Tables

#### accounts
```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    api_token VARCHAR(255) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    monthly_limit INTEGER DEFAULT 100,
    monthly_extractions INTEGER DEFAULT 0,
    total_extractions INTEGER DEFAULT 0,
    enabled_models TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_accounts_api_token ON accounts(api_token);
```

#### templates
```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(100) UNIQUE NOT NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    template_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    country_id INTEGER REFERENCES countries(id),
    fields JSONB NOT NULL,  -- Array of field definitions
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    avg_confidence DECIMAL(5,3) DEFAULT 0.0,
    avg_completeness DECIMAL(5,3) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_templates_account ON templates(account_id);
CREATE INDEX idx_templates_category ON templates(category);
```

#### extractions
```sql
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id VARCHAR(100) UNIQUE NOT NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    template_id VARCHAR(100) REFERENCES templates(template_id),
    filename VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    country_code VARCHAR(10),
    vision_model VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',
    extracted_fields JSONB,  -- JSON extraction results (NO FILES)
    quality_score JSONB,
    quality_grade VARCHAR(2),
    processing_time_ms INTEGER,
    cost_usd DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_extractions_account ON extractions(account_id);
CREATE INDEX idx_extractions_status ON extractions(status);
CREATE INDEX idx_extractions_category ON extractions(category);
```

#### document_tags
```sql
CREATE TABLE document_tags (
    id SERIAL PRIMARY KEY,
    extraction_id VARCHAR(100) REFERENCES extractions(extraction_id),
    tag VARCHAR(100) NOT NULL,
    auto_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tags_extraction ON document_tags(extraction_id);
CREATE INDEX idx_tags_tag ON document_tags(tag);
```

#### api_logs
```sql
CREATE TABLE api_logs (
    id BIGSERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_api_logs_account ON api_logs(account_id);
CREATE INDEX idx_api_logs_created ON api_logs(created_at);
```

### Multi-Tenant Isolation

All queries automatically filter by `account_id`:

```python
# Example: Get templates for authenticated account
templates = db.query(Template).filter(
    Template.account_id == account.id
).all()

# Prevents cross-account data access
# Account 1 cannot see Account 2's templates
```

---

## API Documentation

### Authentication

All API requests require Bearer token authentication:

```bash
curl -H "Authorization: Bearer aiv_abc123..." \
     https://api.example.com/api/v1/extractions/
```

**Token Format**: `aiv_{32_random_characters}`

### Core Endpoints

#### POST /api/v1/extractions/extract
Extract data from a document.

**Request**:
```bash
curl -X POST "https://api.example.com/api/v1/extractions/extract" \
  -H "Authorization: Bearer aiv_your_token" \
  -F "file=@document.pdf" \
  -F "vision_model=gemini-2.0-flash-exp" \
  -F "auto_detect=true"
```

**Response**:
```json
{
  "extraction_id": "ext_abc123",
  "filename": "document.pdf",
  "category": "invoice",
  "country_code": "IE",
  "vision_model": "gemini-2.0-flash-exp",
  "status": "completed",
  "extracted_fields": {
    "invoice_number": "INV-2024-001",
    "total_amount": "€1,234.56",
    "invoice_date": "2024-01-15",
    "vendor_name": "Acme Corp"
  },
  "auto_tags": ["invoice", "acme", "2024", "financial"],
  "quality_score": {
    "completeness": 0.95,
    "avg_confidence": 0.92,
    "quality_grade": "A"
  },
  "processing_time_ms": 2450,
  "cost_usd": 0.0025
}
```

#### POST /api/v1/templates/
Create a custom extraction template.

**Request**:
```json
{
  "name": "Custom Invoice Template",
  "category": "invoice",
  "country_code": "IE",
  "description": "Template for Irish invoices",
  "fields": [
    {
      "name": "invoice_number",
      "type": "string",
      "required": true,
      "description": "Unique invoice identifier"
    },
    {
      "name": "total_amount",
      "type": "currency",
      "required": true
    },
    {
      "name": "line_items",
      "type": "list",
      "required": false,
      "fields": [
        {"name": "description", "type": "string"},
        {"name": "quantity", "type": "number"},
        {"name": "price", "type": "currency"}
      ]
    }
  ]
}
```

#### GET /api/v1/analytics/dashboard?days=30
Get dashboard analytics.

**Response**:
```json
{
  "period_days": 30,
  "overview": {
    "total_extractions": 1250,
    "success_rate": 0.96,
    "avg_confidence": 0.88,
    "total_cost_usd": 3.75
  },
  "model_usage": {
    "gemini-2.0-flash-exp": {
      "count": 1000,
      "total_cost": 2.50
    },
    "gpt-4o": {
      "count": 200,
      "total_cost": 1.00
    },
    "claude-sonnet-4-20250514": {
      "count": 50,
      "total_cost": 0.25
    }
  },
  "account_usage": {
    "monthly_extractions": 1250,
    "monthly_limit": 10000,
    "remaining": 8750
  }
}
```

### Full API Documentation

Interactive API docs available at:
- **Swagger UI**: `https://your-domain.com/docs`
- **ReDoc**: `https://your-domain.com/redoc`

---

## Deployment

### Prerequisites

- AWS EC2 instance (t3.medium or larger recommended)
- Ubuntu 22.04 LTS
- Domain name with DNS configured
- Email for SSL certificate
- API keys for vision models (Gemini, OpenAI, Claude)

### Quick Deploy

```bash
# Clone repository
git clone https://github.com/your-org/aivision.git
cd aivision

# Set environment variables
export DB_PASSWORD="your_secure_password"
export DOMAIN_NAME="api.yourdomain.com"
export ADMIN_EMAIL="admin@yourdomain.com"
export GEMINI_API_KEY="your_gemini_key"
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"

# Run deployment script
chmod +x deploy/scripts/deploy.sh
sudo ./deploy/scripts/deploy.sh

# Test deployment
./deploy/scripts/test_deployment.sh https://api.yourdomain.com
```

### Storage Configuration

AIVision stores **ONLY JSON** results in the database. Original files are **NOT** persisted:

```bash
# .env configuration
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false
STORE_EXTRACTED_IMAGES=false
```

This ensures:
- ✅ Lower storage costs
- ✅ Better privacy/security
- ✅ Faster cleanup
- ✅ GDPR/compliance friendly

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=postgresql://aivision:password@localhost/aivision
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aivision
DB_USER=aivision
DB_PASSWORD=your_secure_password

# API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Storage (JSON ONLY - NO FILE STORAGE)
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false
STORE_EXTRACTED_IMAGES=false

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=50
```

---

## Usage Examples

### Python SDK

```python
import requests

API_BASE = "https://api.yourdomain.com"
API_TOKEN = "aiv_your_token_here"

headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# Extract document with auto-detection
with open("invoice.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "vision_model": "gemini-2.0-flash-exp",
        "auto_detect": True
    }

    response = requests.post(
        f"{API_BASE}/api/v1/extractions/extract",
        headers=headers,
        files=files,
        data=data
    )

    result = response.json()
    print(f"Extracted {len(result['extracted_fields'])} fields")
    print(f"Quality grade: {result['quality_score']['quality_grade']}")
```

### JavaScript/TypeScript

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api.yourdomain.com',
  headers: {
    'Authorization': `Bearer aiv_your_token_here`
  }
});

// Extract document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('vision_model', 'gemini-2.0-flash-exp');
formData.append('auto_detect', 'true');

const response = await apiClient.post('/api/v1/extractions/extract', formData);
console.log('Extraction ID:', response.data.extraction_id);
console.log('Quality grade:', response.data.quality_score.quality_grade);
```

---

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_extractions_created_at ON extractions(created_at);
CREATE INDEX idx_extractions_account_status ON extractions(account_id, status);
CREATE INDEX idx_templates_account_category ON templates(account_id, category);

-- Vacuum regularly
VACUUM ANALYZE extractions;
VACUUM ANALYZE api_logs;

-- Archive old logs
DELETE FROM api_logs WHERE created_at < NOW() - INTERVAL '90 days';
```

### Model Selection for Performance

- **Gemini 2.0 Flash**: Fastest (2-3s), lowest cost
- **GPT-4o**: Moderate speed (4-6s), higher accuracy
- **Claude Sonnet 4**: Slower (6-8s), best for complex docs

**Recommendation**: Use Gemini as default, fall back to GPT-4o for low confidence results.

---

## Security

### Authentication

- **Bearer Token**: `aiv_` prefixed, 32 random characters
- **Token Storage**: Hashed in database
- **Token Rotation**: Users can regenerate tokens
- **Rate Limiting**: 60 requests/minute per account

### Data Protection

- **Multi-Tenant Isolation**: Row-level security by account_id
- **No File Storage**: Original documents deleted after extraction
- **HTTPS Only**: All traffic encrypted with TLS 1.3
- **Webhook Signatures**: HMAC-SHA256 verification

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U aivision -d aivision

# Check logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 2. Vision API Errors

```python
# Gemini API rate limit
# Error: 429 Too Many Requests
# Solution: Add exponential backoff with retry logic
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/aivision.git
cd aivision

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb aivision
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_extraction.py::test_auto_classify
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: https://github.com/your-org/aivision/issues
- **Email**: support@aivision.example.com

---

Built with ❤️ for the document automation community.
