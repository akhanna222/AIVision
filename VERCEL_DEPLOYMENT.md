# Vercel Deployment Guide for AIVision

This guide covers deploying AIVision to Vercel, inspired by rapid SaaS deployment strategies. Since AIVision is a full-stack application with a Python backend and React frontend, we'll explore multiple deployment architectures.

## Table of Contents

1. [Deployment Architecture Options](#deployment-architecture-options)
2. [Option 1: Frontend on Vercel + Backend on Railway/Render](#option-1-frontend-on-vercel--backend-on-railwayrender)
3. [Option 2: Full Monorepo on Vercel](#option-2-full-monorepo-on-vercel)
4. [Environment Variables Setup](#environment-variables-setup)
5. [Database Setup (Vercel Postgres / Neon)](#database-setup)
6. [Quick Start Checklist](#quick-start-checklist)

---

## Deployment Architecture Options

### Understanding the Stack

AIVision consists of:
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Backend**: Python FastAPI + PostgreSQL + Redis
- **External APIs**: Google Gemini, OpenAI, Anthropic

### Recommended Architectures

| Architecture | Best For | Complexity |
|--------------|----------|------------|
| Frontend on Vercel + Backend on Railway | Production workloads | Medium |
| Full Stack on Vercel (Serverless) | Quick demos, low traffic | Low |
| Frontend on Vercel + Backend on Render | Cost-effective production | Medium |

---

## Option 1: Frontend on Vercel + Backend on Railway/Render

**Recommended for production use.** This separates concerns and allows the FastAPI backend to run as a persistent service with proper database connections.

### Step 1: Deploy Backend to Railway

1. **Create Railway Account**: Go to [railway.app](https://railway.app)

2. **Create New Project**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login to Railway
   railway login

   # Initialize project in AIVision directory
   cd /path/to/AIVision
   railway init
   ```

3. **Add PostgreSQL and Redis**:
   - In Railway dashboard, click "New" → "Database" → "PostgreSQL"
   - Click "New" → "Database" → "Redis"

4. **Configure Backend Service**:

   Create `railway.json` in project root:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile.backend"
     },
     "deploy": {
       "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
       "healthcheckPath": "/health",
       "restartPolicyType": "ON_FAILURE"
     }
   }
   ```

5. **Set Environment Variables** in Railway dashboard (see [Environment Variables](#environment-variables-setup))

6. **Deploy**:
   ```bash
   railway up
   ```

7. **Get Backend URL**: Copy your Railway backend URL (e.g., `https://aivision-backend.up.railway.app`)

### Step 2: Deploy Frontend to Vercel

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Create Vercel Configuration**:

   Create `frontend/vercel.json`:
   ```json
   {
     "version": 2,
     "name": "aivision-frontend",
     "builds": [
       {
         "src": "package.json",
         "use": "@vercel/static-build",
         "config": {
           "distDir": "dist"
         }
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "https://YOUR_BACKEND_URL/api/$1"
       },
       {
         "src": "/(.*)",
         "dest": "/$1"
       }
     ],
     "env": {
       "VITE_API_URL": "https://YOUR_BACKEND_URL"
     }
   }
   ```

3. **Update Frontend API Configuration**:

   Ensure `frontend/src/services/api.ts` uses environment variable:
   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   ```

4. **Deploy to Vercel**:
   ```bash
   cd frontend
   vercel --prod
   ```

5. **Set Environment Variables in Vercel Dashboard**:
   - Go to Project Settings → Environment Variables
   - Add `VITE_API_URL` = your Railway backend URL

---

## Option 2: Full Monorepo on Vercel

Deploy everything to Vercel using serverless functions for the backend. Best for demos and low-traffic applications.

### Step 1: Create Vercel Project Structure

Create `vercel.json` in project root:

```json
{
  "version": 2,
  "name": "aivision",
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "frontend/dist"
      }
    },
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "functions": {
    "api/index.py": {
      "memory": 1024,
      "maxDuration": 60
    }
  }
}
```

### Step 2: Create Serverless API Entry Point

Create `api/index.py`:

```python
"""
Vercel Serverless Function Entry Point for AIVision API
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Import your FastAPI app
from app.main import app as fastapi_app

# Create a wrapper for serverless
handler = Mangum(fastapi_app, lifespan="off")

def main(request, context):
    """Vercel serverless handler"""
    return handler(request, context)
```

### Step 3: Update Requirements for Vercel

Create `api/requirements.txt`:

```txt
fastapi>=0.109.0
mangum>=0.17.0
pydantic>=2.5.3
google-generativeai>=0.3.2
openai>=1.10.0
anthropic>=0.18.1
python-multipart>=0.0.6
pillow>=10.2.0
httpx>=0.26.0
python-dotenv>=1.0.1
```

### Step 4: Use Vercel Postgres

1. **Enable Vercel Postgres**:
   - Go to Vercel Dashboard → Storage → Create Database → Postgres

2. **Update Database Configuration**:

   Vercel automatically injects `POSTGRES_URL`. Update `app/config.py`:
   ```python
   import os

   DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
   ```

### Step 5: Deploy

```bash
# From project root
vercel --prod
```

---

## Environment Variables Setup

### Required Variables

Set these in Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_URL` | Database connection (auto-set if using Vercel Postgres) | `postgres://...` |
| `GOOGLE_API_KEY` | Google Gemini API key | `AIza...` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) | `sk-ant-...` |
| `SECRET_KEY` | JWT signing secret | Random 32-char string |
| `ENVIRONMENT` | Deployment environment | `production` |

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Setting Variables via CLI

```bash
# Set production environment variables
vercel env add GOOGLE_API_KEY production
vercel env add SECRET_KEY production
vercel env add ENVIRONMENT production
```

---

## Database Setup

### Option A: Vercel Postgres (Recommended)

1. Go to Vercel Dashboard → Storage
2. Click "Create Database" → "Postgres"
3. Select your region (choose closest to your users)
4. Connect to your project
5. Vercel automatically injects `POSTGRES_URL`

### Option B: Neon Postgres (Free Tier)

1. Create account at [neon.tech](https://neon.tech)
2. Create new project
3. Copy connection string
4. Add to Vercel: `DATABASE_URL` = your Neon connection string

### Option C: Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Go to Settings → Database → Connection string
3. Add to Vercel environment variables

### Run Migrations

After database is connected:

```bash
# Connect to Vercel environment
vercel env pull .env.local

# Run migrations
alembic upgrade head
```

---

## Quick Start Checklist

### Pre-Deployment

- [ ] Create Vercel account at [vercel.com](https://vercel.com)
- [ ] Install Vercel CLI: `npm i -g vercel`
- [ ] Get API keys (at minimum, Google Gemini API key)
- [ ] Fork/clone AIVision repository

### Deployment Steps

```bash
# 1. Clone and enter project
git clone <your-repo>
cd AIVision

# 2. Login to Vercel
vercel login

# 3. Create Vercel Postgres (via dashboard or CLI)
vercel storage create postgres

# 4. Set environment variables
vercel env add GOOGLE_API_KEY
vercel env add SECRET_KEY
vercel env add ENVIRONMENT

# 5. Deploy
vercel --prod

# 6. Verify deployment
curl https://your-app.vercel.app/api/v1/health
```

### Post-Deployment

- [ ] Test document upload functionality
- [ ] Verify API responses
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring (Vercel Analytics)

---

## Custom Domain Setup

1. Go to Vercel Dashboard → Project → Settings → Domains
2. Add your domain (e.g., `aivision.yourdomain.com`)
3. Update DNS records as instructed by Vercel
4. SSL certificate is automatically provisioned

---

## Troubleshooting

### Common Issues

**Build Fails - Python Dependencies**
```
Error: Cannot find module 'xyz'
```
Solution: Ensure all dependencies are in `api/requirements.txt`

**Database Connection Error**
```
Error: Connection refused
```
Solution: Verify `POSTGRES_URL` is set correctly in environment variables

**CORS Errors**
Solution: Ensure backend CORS settings include your Vercel domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Function Timeout**
Solution: For long-running document processing, consider:
- Increasing function timeout in `vercel.json` (max 60s on Hobby, 300s on Pro)
- Using background jobs with Vercel Cron or external queue

### Logs and Debugging

```bash
# View deployment logs
vercel logs your-app.vercel.app

# View function logs in real-time
vercel logs your-app.vercel.app --follow
```

---

## Production Recommendations

1. **Use Vercel Pro** for longer function timeouts (300s vs 60s)
2. **Enable Vercel Analytics** for performance monitoring
3. **Set up Error Tracking** with Sentry integration
4. **Configure Caching** for static assets
5. **Use Edge Functions** for low-latency API routes

---

## Cost Estimation

| Service | Free Tier | Paid |
|---------|-----------|------|
| Vercel Hosting | 100GB bandwidth/month | $20/month Pro |
| Vercel Postgres | 256MB storage | $20/month |
| Google Gemini API | 60 requests/min | Pay per use |
| Total (Low Traffic) | **$0** | ~$40/month |

---

## Next Steps

1. **Add Authentication**: Integrate Firebase Auth or Clerk for user management
2. **Add Payments**: Integrate Stripe for monetization (see original SaaS guide)
3. **Add Monitoring**: Set up Vercel Analytics and Sentry
4. **Scale**: Upgrade to Vercel Pro for higher limits

---

## References

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Functions](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)
- [FastAPI on Vercel](https://fastapi.tiangolo.com/deployment/)
- [Original SaaS Build Guide](https://www.docupipe.ai/blog/saas-guide-pdf-redaction)
