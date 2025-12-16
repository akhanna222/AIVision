# 🚀 Quick Start: Running on AWS EC2

Complete guide to deploy AIVision OCR service on AWS EC2 in under 30 minutes.

---

## 📋 Prerequisites

- AWS Account
- SSH key pair
- At least ONE API key (Gemini is FREE!)

---

## 🔑 Step 1: Get Your API Keys (5 minutes)

You need **at least ONE** API key. **Gemini is FREE** and works great!

### Option A: Google Gemini (FREE) ⭐ Recommended

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. **Cost**: FREE (60 requests/minute)

### Option B: OpenAI GPT-4o (Paid)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create account + add payment method
3. Create API key (starts with `sk-...`)
4. **Cost**: ~$0.30 per 1000 documents (GPT-4o-mini)

### Option C: Anthropic Claude (Paid)

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create account + add payment method
3. Create API key (starts with `sk-ant-...`)
4. **Cost**: ~$0.50 per 1000 documents (Haiku 4)

💡 **Best Setup**: Gemini (free) + GPT-4o-mini ($0.30/1000 docs) for fallback

---

## 🖥️ Step 2: Launch EC2 Instance (5 minutes)

### Instance Configuration

1. **Go to AWS EC2 Console** → Launch Instance

2. **Configure**:
   ```
   Name: aivision-ocr
   AMI: Ubuntu Server 22.04 LTS
   Instance Type: t3.medium (2 vCPU, 4GB RAM)
   Storage: 30 GB gp3 SSD
   Key pair: Select or create new
   ```

3. **Security Group** (IMPORTANT):

   | Type | Port | Source | Description |
   |------|------|--------|-------------|
   | SSH | 22 | Your IP | SSH access |
   | HTTP | 80 | 0.0.0.0/0 | Web access |
   | HTTPS | 443 | 0.0.0.0/0 | Secure web |
   | Custom | 8000 | 0.0.0.0/0 | API (temp) |

4. **Launch Instance** and wait 2 minutes

5. **Get Public IP**: Copy from instance details

---

## ⚙️ Step 3: Connect and Install (10 minutes)

### Connect to Instance

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Clone Repository

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clone repository
cd /opt
sudo mkdir aivision
sudo chown ubuntu:ubuntu aivision
cd aivision
git clone https://github.com/your-org/AIVision.git .
```

### Set Environment Variables

```bash
# Create .env file
nano .env
```

Paste this configuration (update with YOUR API keys):

```bash
# Database (will be auto-created)
DATABASE_URL=postgresql://aivision:auto-generated-password@localhost:5432/aivision

# API Keys - Add at least ONE (Gemini is FREE!)
GEMINI_API_KEY=AIzaSy_your_actual_key_here
OPENAI_API_KEY=sk-your_key_here_optional
ANTHROPIC_API_KEY=sk-ant-your_key_here_optional

# Application Settings
SECRET_KEY=will-be-auto-generated
APP_ENV=production
DEBUG=false

# Multi-Model Extraction
DEFAULT_EXTRACTION_STRATEGY=sequential
CONFIDENCE_THRESHOLD=0.80
MAX_MODELS_TO_TRY=3

# Server (defaults - no need to change)
BACKEND_PORT=8000
MAX_FILE_SIZE_MB=50
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

---

## 🚀 Step 4: Run Deployment Script (10 minutes)

### One-Command Deployment

```bash
# Make script executable
sudo chmod +x deploy/scripts/deploy.sh

# Export your API keys
export GEMINI_API_KEY="AIzaSy_your_key"
export OPENAI_API_KEY="sk-your_key"  # Optional
export ANTHROPIC_API_KEY="sk-ant-your_key"  # Optional

# Run deployment (handles everything!)
sudo -E ./deploy/scripts/deploy.sh
```

### What the Script Does:

✅ Checks and frees required ports (8000, 3000, 5432, 80, 443)
✅ Installs Python, Node.js, PostgreSQL, Nginx
✅ Creates database with secure password
✅ Installs Python dependencies
✅ Runs database migrations
✅ Runs tests
✅ Builds React frontend
✅ Configures systemd services
✅ Sets up Nginx reverse proxy
✅ Starts all services

**Wait 5-10 minutes** for completion.

---

## ✅ Step 5: Verify Installation (2 minutes)

### Check Services

```bash
# Backend
sudo systemctl status aivision

# Database
sudo systemctl status postgresql

# Web server
sudo systemctl status nginx

# All should show "active (running)" in green
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### Access Web Interface

Open browser: `http://YOUR_EC2_PUBLIC_IP`

### 🌐 Access Public Template Builder & Extraction UIs

The deployment includes public UIs that don't require authentication:

**Template Builder** (create custom OCR templates):
```
http://YOUR_EC2_PUBLIC_IP/template-builder
```

**Simple Extraction** (extract data using templates):
```
http://YOUR_EC2_PUBLIC_IP/simple-extract
```

**📖 For detailed public UI setup and external access, see**: [`README_PUBLIC_UI_ACCESS.md`](README_PUBLIC_UI_ACCESS.md)

This guide covers:
- Exposing UIs publicly with proper CORS
- Setting up custom domains
- SSL certificate configuration
- Security best practices
- Embedding in your applications

---

## 🎯 Step 6: Create First Account & Test (5 minutes)

### Create Account

```bash
curl -X POST http://YOUR_EC2_IP/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Account",
    "email": "test@example.com",
    "plan": "professional"
  }'
```

**Save the API token** from the response!

### Test Single-Model Extraction

```bash
curl -X POST http://YOUR_EC2_IP/api/v1/extractions/extract \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@invoice.pdf" \
  -F "vision_model=gemini-2.0-flash-exp" \
  -F "auto_detect=true"
```

### Test Multi-Model Extraction 🎉

```bash
curl -X POST http://YOUR_EC2_IP/api/v1/extractions/extract-multi-model \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@invoice.pdf" \
  -F "models=gemini-2.0-flash-exp,gpt-4o" \
  -F "strategy=hybrid" \
  -F "confidence_threshold=0.80"
```

**Response includes**:
- `field_model_map`: Which model extracted each field
- `extraction_summary`: User-friendly summary
- `models_tried`: All models attempted
- `missing_fields`: Fields that couldn't be extracted

---

## 🌐 Optional: Setup Domain & SSL (5 minutes)

If you have a domain name:

```bash
# Install SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts, certificate is auto-renewed
```

Now access via: `https://yourdomain.com`

---

## 📊 Monitoring & Logs

### View Logs

```bash
# Backend logs (real-time)
sudo journalctl -u aivision -f

# Nginx access logs
sudo tail -f /var/log/nginx/aivision_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/aivision_error.log

# Application logs
sudo tail -f /var/log/aivision/error.log
```

### Service Management

```bash
# Restart services
sudo systemctl restart aivision
sudo systemctl restart nginx

# Stop services
sudo systemctl stop aivision

# Start services
sudo systemctl start aivision

# Check status
sudo systemctl status aivision
```

---

## 🔧 Troubleshooting

### Port Already in Use

The deployment script automatically handles this, but if needed:

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or re-run deployment script
sudo ./deploy/scripts/deploy.sh
```

### Can't Connect to Database

```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Restart if needed
sudo systemctl restart postgresql

# View credentials
cat /opt/aivision/.db_credentials
```

### API Key Errors

```bash
# Verify API key is set
sudo cat /opt/aivision/.env | grep API_KEY

# Test Gemini API
curl "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp?key=YOUR_KEY"
```

### Service Won't Start

```bash
# Check errors
sudo journalctl -u aivision -n 50

# Check if ports are free
sudo lsof -i :8000

# Restart service
sudo systemctl restart aivision
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce Gunicorn workers
sudo nano /opt/aivision/gunicorn.conf.py
# Change: workers = 2

# Restart
sudo systemctl restart aivision
```

---

## 🎯 Multi-Model Extraction Strategies

### Sequential (Default)
Try models one by one until confidence threshold is met:
```bash
-F "strategy=sequential"
-F "models=gemini-2.0-flash-exp,gpt-4o,claude-sonnet-4-20250514"
```
**Use when**: Cost-conscious, want to minimize API calls

### Parallel
Run all models simultaneously, pick best per field:
```bash
-F "strategy=parallel"
-F "models=gemini-2.0-flash-exp,gpt-4o"
```
**Use when**: Maximum accuracy needed, speed over cost

### Hybrid (Recommended)
Primary model + parallel retry for low-confidence fields:
```bash
-F "strategy=hybrid"
-F "models=gemini-2.0-flash-exp,gpt-4o-mini"
```
**Use when**: Balance between cost and accuracy

---

## 💰 Cost Optimization

### Free Tier Setup (0 cost)
```bash
# Use only Gemini (60 req/min free)
-F "models=gemini-2.0-flash-exp"
```

### Budget Setup (~$0.30/1000 docs)
```bash
# Gemini + GPT-4o-mini fallback
-F "models=gemini-2.0-flash-exp,gpt-4o-mini"
-F "strategy=hybrid"
```

### High Accuracy (~$6/1000 docs)
```bash
# Multiple premium models
-F "models=gpt-4o,claude-sonnet-4-20250514"
-F "strategy=parallel"
```

---

## 📚 API Documentation

Once deployed, access interactive API docs:

- **Swagger UI**: `http://YOUR_EC2_IP/docs`
- **ReDoc**: `http://YOUR_EC2_IP/redoc`
- **OpenAPI JSON**: `http://YOUR_EC2_IP/openapi.json`

---

## 🔐 Security Checklist

- [ ] Change default PostgreSQL password
- [ ] Restrict SSH to your IP only (Security Group)
- [ ] Enable SSL with Let's Encrypt (if using domain)
- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Never commit API keys to git
- [ ] Enable AWS CloudWatch monitoring
- [ ] Setup regular database backups
- [ ] Use Elastic IP for static address

---

## 🆘 Need Help?

- **Full Documentation**: See `AWS_EC2_DEPLOYMENT.md` for comprehensive guide
- **Local Development**: See `README_LOCAL_WINDOWS.md` for Windows setup
- **API Reference**: `/docs` endpoint on your server
- **Logs**: `sudo journalctl -u aivision -f`

---

## 📝 Quick Reference

```bash
# Service commands
sudo systemctl status aivision
sudo systemctl restart aivision
sudo systemctl stop aivision

# View logs
sudo journalctl -u aivision -f

# Check ports
sudo lsof -i :8000

# Database access
sudo -u postgres psql aivision

# Update code
cd /opt/aivision
git pull
sudo systemctl restart aivision
```

---

**🎉 Congratulations!** Your AIVision OCR service is running on AWS EC2 with multi-model extraction support!

**Estimated Total Time**: 30-40 minutes
**Estimated Monthly Cost**: $20-30 (EC2 t3.medium) + API usage
