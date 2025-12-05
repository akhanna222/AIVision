# AWS EC2 Deployment Guide

Complete guide to deploying AIVision OCR service on AWS EC2 with production-ready configuration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Required API Keys](#required-api-keys)
- [EC2 Instance Setup](#ec2-instance-setup)
- [Security Groups & Ports](#security-groups--ports)
- [Installation & Deployment](#installation--deployment)
- [Environment Configuration](#environment-configuration)
- [Running the Service](#running-the-service)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- AWS Account with EC2 access
- SSH key pair for EC2 access
- Domain name (optional, for production)
- API keys for AI vision models (see below)

### Recommended EC2 Instance

- **Instance Type**: `t3.medium` or larger (2 vCPU, 4GB RAM minimum)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 30GB+ SSD
- **Region**: Choose based on your users' location

---

## Required API Keys

AIVision supports multiple AI vision models. You need at least one API key, but having multiple enables the multi-model extraction feature.

### 1. Google Gemini API Key

**Model**: `gemini-2.0-flash-exp`

**How to Get**:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key (starts with `AIza...`)

**Pricing**: Free tier available (60 requests/minute)

**Environment Variable**: `GEMINI_API_KEY`

### 2. OpenAI API Key

**Models**: `gpt-4o`, `gpt-4o-mini`

**How to Get**:
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create account and add payment method
3. Create new API key
4. Copy the key (starts with `sk-...`)

**Pricing**: Pay-as-you-go (GPT-4o: ~$5/1M input tokens, GPT-4o-mini: ~$0.15/1M input tokens)

**Environment Variable**: `OPENAI_API_KEY`

### 3. Anthropic Claude API Key

**Models**: `claude-sonnet-4-20250514`, `claude-haiku-4-20250514`

**How to Get**:
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create account and add payment method
3. Go to API Keys section
4. Create new API key
5. Copy the key (starts with `sk-ant-...`)

**Pricing**: Pay-as-you-go (Claude Sonnet 4: ~$3/1M input tokens, Claude Haiku 4: ~$0.25/1M input tokens)

**Environment Variable**: `ANTHROPIC_API_KEY`

### Cost Estimation

For document extraction (typical document = ~1500 tokens):

| Model | Cost per 1000 docs | Recommended For |
|-------|-------------------|-----------------|
| Gemini 2.0 Flash | **FREE** (up to quota) | Development, high-volume |
| GPT-4o Mini | ~$0.30 | Production, cost-effective |
| GPT-4o | ~$9.00 | High accuracy required |
| Claude Haiku 4 | ~$0.50 | Balanced performance |
| Claude Sonnet 4 | ~$6.00 | Complex documents |

**Recommendation**: Start with Gemini 2.0 Flash (free) + GPT-4o Mini as fallback ($0.30/1000 docs).

---

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. **Go to AWS EC2 Console** → Launch Instance

2. **Configure Instance**:
   ```
   Name: aivision-ocr-production
   AMI: Ubuntu Server 22.04 LTS
   Instance Type: t3.medium (2 vCPU, 4GB RAM)
   Key pair: Select or create new
   ```

3. **Storage**:
   - Root volume: 30 GB gp3 SSD

4. **Network Settings** (configure in next step)

### Step 2: Security Groups & Ports

Create a security group with these rules:

#### Inbound Rules

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP/0.0.0.0/0 | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS traffic |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | FastAPI backend |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | React frontend (dev) |
| Custom TCP | TCP | 5432 | Your IP only | PostgreSQL (if remote) |

**Security Note**:
- For production, restrict port 22 (SSH) to your IP only
- Use 80/443 with reverse proxy (Nginx) instead of exposing 8000/3000
- Never expose port 5432 (PostgreSQL) publicly

#### Outbound Rules

Allow all outbound traffic (default).

### Step 3: Elastic IP (Optional but Recommended)

1. Allocate Elastic IP: EC2 → Elastic IPs → Allocate
2. Associate with your instance
3. This gives you a static IP that won't change on reboot

---

## Installation & Deployment

### Step 1: Connect to EC2

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Update system
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Dependencies

```bash
# Install required packages
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    build-essential \
    libpq-dev

# Install Node.js 18+ (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Step 3: Setup PostgreSQL

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE aivision;
CREATE USER aivision WITH PASSWORD 'CHANGE_THIS_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;
ALTER DATABASE aivision OWNER TO aivision;
\q
EOF
```

**Important**: Change `'CHANGE_THIS_PASSWORD'` to a strong password!

### Step 4: Clone Repository

```bash
# Create app directory
sudo mkdir -p /opt/aivision
sudo chown ubuntu:ubuntu /opt/aivision

# Clone repository
cd /opt/aivision
git clone https://github.com/your-org/AIVision.git .
```

### Step 5: Check and Free Ports

The deployment script will automatically check and free ports if they're in use:

```bash
# Check if ports are available
sudo lsof -i :8000  # Backend
sudo lsof -i :3000  # Frontend
sudo lsof -i :5432  # PostgreSQL

# If ports are occupied, the deployment script will:
# 1. Identify the process using the port
# 2. Stop the process gracefully
# 3. Free the port for AIVision
```

---

## Environment Configuration

### Step 1: Create Environment File

```bash
cd /opt/aivision
cp .env.example .env
nano .env
```

### Step 2: Configure Environment Variables

```bash
# =====================
# REQUIRED CONFIGURATION
# =====================

# Database
DATABASE_URL=postgresql://aivision:YOUR_DB_PASSWORD@localhost:5432/aivision

# API Keys (provide at least one)
GEMINI_API_KEY=AIzaSy...your-gemini-key
OPENAI_API_KEY=sk-...your-openai-key
ANTHROPIC_API_KEY=sk-ant-...your-claude-key

# Application
SECRET_KEY=$(openssl rand -hex 32)
APP_ENV=production
DEBUG=false

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# CORS (Update with your domain)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# =====================
# OPTIONAL CONFIGURATION
# =====================

# File Upload
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=["pdf","png","jpg","jpeg","tiff","bmp"]

# Storage (JSON-only by default)
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false

# Model Defaults
DEFAULT_VISION_MODEL=gemini-2.0-flash-exp
ENABLED_MODELS=["gemini-2.0-flash-exp","gpt-4o","gpt-4o-mini","claude-sonnet-4-20250514"]

# Multi-Model Extraction
DEFAULT_EXTRACTION_STRATEGY=sequential
CONFIDENCE_THRESHOLD=0.80
FIELD_CONFIDENCE_THRESHOLD=0.70
MAX_MODELS_TO_TRY=3

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
BURST_LIMIT=10

# Webhooks
ENABLE_WEBHOOKS=true
WEBHOOK_TIMEOUT_SECONDS=30
WEBHOOK_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/aivision/app.log

# Monitoring
SENTRY_DSN=  # Optional: Add Sentry DSN for error tracking
```

### Step 3: Secure Environment File

```bash
chmod 600 .env
```

---

## Running the Service

### Option 1: Automated Deployment Script (Recommended)

```bash
cd /opt/aivision
sudo chmod +x deploy/scripts/deploy.sh
sudo ./deploy/scripts/deploy.sh
```

The script will:
1. ✓ Check and free required ports (8000, 3000, 5432)
2. ✓ Install Python dependencies
3. ✓ Run database migrations
4. ✓ Build frontend
5. ✓ Run tests
6. ✓ Configure systemd services
7. ✓ Start backend and frontend
8. ✓ Setup Nginx reverse proxy
9. ✓ Configure SSL (if domain provided)

### Option 2: Manual Setup

#### Backend Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/aivision-backend.service
```

```ini
[Unit]
Description=AIVision OCR Backend
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/aivision
Environment="PATH=/opt/aivision/venv/bin"
EnvironmentFile=/opt/aivision/.env
ExecStart=/opt/aivision/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Start backend
sudo systemctl daemon-reload
sudo systemctl enable aivision-backend
sudo systemctl start aivision-backend
```

#### Frontend Service

```bash
# Build frontend
cd /opt/aivision/frontend
npm install
npm run build

# Create systemd service
sudo nano /etc/systemd/system/aivision-frontend.service
```

```ini
[Unit]
Description=AIVision OCR Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/aivision/frontend
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Start frontend
sudo systemctl daemon-reload
sudo systemctl enable aivision-frontend
sudo systemctl start aivision-frontend
```

### Option 3: Docker Deployment

```bash
cd /opt/aivision
docker-compose -f docker-compose.prod.yml up -d
```

---

## Nginx Reverse Proxy (Production)

### Setup Nginx

```bash
sudo nano /etc/nginx/sites-available/aivision
```

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Monitoring & Logs

### System Logs

```bash
# Backend logs
sudo journalctl -u aivision-backend -f

# Frontend logs
sudo journalctl -u aivision-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Application Logs

```bash
# Application logs
tail -f /var/log/aivision/app.log
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database health
sudo -u postgres psql -d aivision -c "SELECT 1;"
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or use the automated script
sudo ./deploy/scripts/deploy.sh  # Automatically frees ports
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U aivision -d aivision -h localhost

# Reset password if needed
sudo -u postgres psql -c "ALTER USER aivision WITH PASSWORD 'new_password';"
```

### API Key Errors

```bash
# Verify API keys are set
cat .env | grep API_KEY

# Test Gemini API
curl "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp?key=YOUR_KEY"

# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"

# Test Anthropic API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce Uvicorn workers in .env
UVICORN_WORKERS=2  # Instead of 4

# Or upgrade instance type
```

### Nginx 502 Bad Gateway

```bash
# Check backend is running
sudo systemctl status aivision-backend

# Check backend health
curl http://localhost:8000/health

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Performance Tuning

### PostgreSQL Tuning

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

```ini
# For 4GB RAM instance
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

```bash
sudo systemctl restart postgresql
```

### Uvicorn Workers

For `t3.medium` (2 vCPU):
```
UVICORN_WORKERS=2-4
```

For `t3.large` (2 vCPU):
```
UVICORN_WORKERS=4-6
```

---

## Backup & Recovery

### Database Backup

```bash
# Manual backup
sudo -u postgres pg_dump aivision > backup_$(date +%Y%m%d).sql

# Automated daily backup
echo "0 2 * * * sudo -u postgres pg_dump aivision > /backups/aivision_\$(date +\%Y\%m\%d).sql" | crontab -
```

### Restore Database

```bash
sudo -u postgres psql aivision < backup_20251205.sql
```

---

## Scaling Recommendations

### Vertical Scaling (Single Instance)

| Users | Instance Type | vCPU | RAM | Storage |
|-------|--------------|------|-----|---------|
| < 100 | t3.medium | 2 | 4GB | 30GB |
| 100-500 | t3.large | 2 | 8GB | 50GB |
| 500-2000 | t3.xlarge | 4 | 16GB | 100GB |
| 2000+ | t3.2xlarge | 8 | 32GB | 200GB |

### Horizontal Scaling (Multiple Instances)

1. **Load Balancer**: Use AWS Application Load Balancer
2. **Database**: Amazon RDS PostgreSQL (managed)
3. **Storage**: Amazon S3 for file storage
4. **Cache**: Amazon ElastiCache Redis
5. **Auto Scaling**: EC2 Auto Scaling Groups

---

## Security Checklist

- [ ] Strong database password
- [ ] `.env` file permissions set to 600
- [ ] Firewall configured (only necessary ports open)
- [ ] SSH restricted to specific IPs
- [ ] SSL/TLS enabled (Let's Encrypt)
- [ ] API keys stored securely (not in code)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Log monitoring enabled
- [ ] Backup strategy in place
- [ ] Rate limiting configured

---

## Support & Resources

- **Documentation**: [Full Docs](./README.md)
- **Local Development**: [Local Setup](./LOCAL_DEVELOPMENT.md)
- **API Reference**: http://your-domain.com:8000/docs
- **GitHub Issues**: Report bugs and feature requests

---

## Quick Reference Commands

```bash
# Start services
sudo systemctl start aivision-backend aivision-frontend

# Stop services
sudo systemctl stop aivision-backend aivision-frontend

# Restart services
sudo systemctl restart aivision-backend aivision-frontend

# View logs
sudo journalctl -u aivision-backend -f

# Check status
sudo systemctl status aivision-backend
sudo systemctl status aivision-frontend

# Health check
curl http://localhost:8000/health

# Free ports
sudo lsof -i :8000 && sudo kill -9 $(sudo lsof -t -i:8000)
```

---

**Last Updated**: December 5, 2025
