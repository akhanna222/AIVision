# 🚀 Deploying AIVision to epingu.org

Quick deployment guide for setting up AIVision OCR service on AWS EC2 with the epingu.org domain.

---

## 📋 Prerequisites

- AWS EC2 instance running Ubuntu 22.04
- Access to epingu.org DNS settings
- SSH key for EC2 access
- At least one API key (Gemini is FREE!)

---

## 🌐 Domain Configuration

We'll use a subdomain for better organization:

**Recommended**: `ocr.epingu.org`

This keeps your main domain free and makes the purpose clear.

---

## Step 1: Configure DNS for epingu.org

### Option A: Using Subdomain (Recommended)

In your DNS provider (where you manage epingu.org), add an A record:

```
Type: A
Name: ocr
Value: YOUR_EC2_ELASTIC_IP
TTL: 300
```

**Result**: `ocr.epingu.org` → Your EC2 instance

### Option B: Using Root Domain

```
Type: A
Name: @
Value: YOUR_EC2_ELASTIC_IP
TTL: 300
```

**Also add www subdomain:**
```
Type: CNAME
Name: www
Value: epingu.org
TTL: 300
```

**Result**: `epingu.org` and `www.epingu.org` → Your EC2 instance

### Get Elastic IP (Recommended)

Static IP that doesn't change when you restart EC2:

1. AWS Console → EC2 → Elastic IPs
2. Allocate Elastic IP address
3. Associate with your EC2 instance
4. Use this IP in DNS settings above

---

## Step 2: Deploy to EC2

### SSH into Instance

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### Clone Repository

```bash
cd /opt
sudo mkdir aivision
sudo chown ubuntu:ubuntu aivision
cd aivision
git clone https://github.com/akhanna222/AIVision.git .
```

### Configure Environment

Create `.env` file:

```bash
nano .env
```

Paste this configuration:

```bash
# Database
DATABASE_URL=postgresql://aivision:auto-generated@localhost:5432/aivision

# API Keys (at least one required - Gemini is FREE!)
GEMINI_API_KEY=AIzaSy_your_actual_key_here
OPENAI_API_KEY=sk-your_key_here_optional
ANTHROPIC_API_KEY=sk-ant-your_key_here_optional

# Application
SECRET_KEY=will-be-auto-generated
APP_ENV=production
DEBUG=false

# CORS - Allow all origins for public API
ALLOWED_ORIGINS=*

# Or restrict to your domains:
# ALLOWED_ORIGINS=https://ocr.epingu.org,https://epingu.org,https://www.epingu.org

# Multi-Model Extraction
DEFAULT_EXTRACTION_STRATEGY=sequential
CONFIDENCE_THRESHOLD=0.80
MAX_MODELS_TO_TRY=3

# Server
BACKEND_PORT=8000
MAX_FILE_SIZE_MB=50
```

### Run Deployment with Domain

```bash
# Set domain for SSL certificate
export DOMAIN="ocr.epingu.org"
export EMAIL="admin@epingu.org"

# Set API keys
export GEMINI_API_KEY="AIzaSy_your_key"
export OPENAI_API_KEY="sk-your_key"  # Optional
export ANTHROPIC_API_KEY="sk-ant-your_key"  # Optional

# Make script executable
sudo chmod +x deploy/scripts/deploy.sh

# Run deployment
sudo -E ./deploy/scripts/deploy.sh
```

The script will:
- Install all dependencies
- Setup PostgreSQL database
- Build React frontend
- Configure Nginx for ocr.epingu.org
- **Install SSL certificate automatically**
- Start all services

Wait 5-10 minutes for completion.

---

## Step 3: Verify DNS Propagation

From your local machine:

```bash
# Check DNS is pointing to EC2
nslookup ocr.epingu.org

# Should show your EC2 Elastic IP
```

Wait a few minutes if DNS hasn't propagated yet.

---

## Step 4: Access Your Public UIs

Once deployed and DNS is propagated:

### Template Builder
```
https://ocr.epingu.org/template-builder
```

Create custom OCR templates without authentication:
1. Choose preset or create custom
2. Add fields with descriptions
3. Save and get instant API endpoint

### Simple Extraction
```
https://ocr.epingu.org/simple-extract
```

Extract data from documents:
1. Select template
2. Upload document (PDF, JPG, PNG)
3. Choose model (Gemini is free!)
4. Extract and view results

### API Documentation
```
https://ocr.epingu.org/docs
```

Interactive API documentation with try-it-now features.

---

## Step 5: Test the APIs

### Save a Template

```bash
curl -X POST https://ocr.epingu.org/api/v1/public/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "invoice",
    "fields": [
      {"name": "invoice_number", "description": "Invoice number"},
      {"name": "total_amount", "description": "Total amount due"},
      {"name": "due_date", "description": "Payment due date"}
    ]
  }'
```

### Extract Using Template

```bash
curl -X POST https://ocr.epingu.org/api/v1/public/extract/invoice \
  -F "file=@my_invoice.pdf" \
  -F "model=gemini-2.0-flash-exp"
```

---

## 🔒 SSL Certificate (Auto-Configured)

The deployment script automatically installs Let's Encrypt SSL certificate for your domain.

### Verify SSL

```bash
# From your local machine
curl -I https://ocr.epingu.org/health

# Should return:
# HTTP/2 200
# ...
```

### Manual SSL Setup (if needed)

If SSL wasn't configured during deployment:

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Install certificate
sudo certbot --nginx -d ocr.epingu.org

# Follow prompts
```

Certificate auto-renews every 90 days.

---

## 📊 Monitor Your Deployment

### Check Services

```bash
# Backend service
sudo systemctl status aivision

# Nginx web server
sudo systemctl status nginx

# Database
sudo systemctl status postgresql

# All should show "active (running)" in green
```

### View Logs

```bash
# Real-time backend logs
sudo journalctl -u aivision -f

# Nginx access logs
sudo tail -f /var/log/nginx/aivision_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/aivision_error.log
```

### Monitor Traffic

```bash
# Count API requests
sudo grep "/api/v1/public" /var/log/nginx/aivision_access.log | wc -l

# Top requesting IPs
sudo awk '{print $1}' /var/log/nginx/aivision_access.log | sort | uniq -c | sort -rn | head -10

# Requests per endpoint
sudo awk '{print $7}' /var/log/nginx/aivision_access.log | sort | uniq -c | sort -rn
```

---

## 🔧 Configuration Files

After deployment, key configuration files:

```bash
# Environment variables
/opt/aivision/.env

# Nginx configuration
/etc/nginx/sites-available/aivision

# SSL certificates
/etc/letsencrypt/live/ocr.epingu.org/

# Database credentials
/opt/aivision/.db_credentials

# Deployment info
/opt/aivision/deployment_info.txt
```

---

## 🔄 Updating Your Deployment

### Pull Latest Code

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Pull updates
cd /opt/aivision
sudo -u aivision git pull

# Restart services
sudo systemctl restart aivision
sudo systemctl restart nginx
```

### Update Dependencies

```bash
cd /opt/aivision

# Backend
sudo -u aivision venv/bin/pip install -r requirements.txt

# Frontend
cd frontend
sudo -u aivision npm install
sudo -u aivision npm run build

# Restart
sudo systemctl restart aivision
```

---

## 🌍 Sharing Your Service

Now you can share these URLs with anyone:

**Template Builder** (no login required):
```
https://ocr.epingu.org/template-builder
```

**Simple Extraction** (no login required):
```
https://ocr.epingu.org/simple-extract
```

**API Endpoint** (for developers):
```
POST https://ocr.epingu.org/api/v1/public/extract/{template_name}
```

---

## 🔐 Security Best Practices

### 1. Keep SSL Updated
Certbot auto-renews, but verify:
```bash
sudo certbot renew --dry-run
```

### 2. Monitor Access
Set up CloudWatch alarms for:
- High CPU usage (>80%)
- High memory usage (>80%)
- Many 4xx/5xx errors

### 3. Rate Limiting
Already configured in Nginx to prevent abuse.

### 4. Regular Backups
Backup your database:
```bash
# Manual backup
sudo -u postgres pg_dump aivision > backup_$(date +%Y%m%d).sql

# Automate with cron
sudo crontab -e
# Add: 0 2 * * * /usr/bin/pg_dump aivision > /backup/aivision_$(date +\%Y\%m\%d).sql
```

### 5. Update System Regularly
```bash
# Monthly updates
sudo apt update && sudo apt upgrade -y
sudo systemctl restart aivision
```

---

## 🆘 Troubleshooting

### DNS Not Resolving

**Problem**: `ocr.epingu.org` doesn't resolve

**Solutions**:
1. Wait 5-10 minutes for DNS propagation
2. Clear DNS cache: `sudo systemd-resolve --flush-caches`
3. Verify DNS settings in your registrar
4. Test with: `nslookup ocr.epingu.org 8.8.8.8`

### SSL Certificate Failed

**Problem**: Certbot couldn't issue certificate

**Solutions**:
1. Ensure DNS points to your EC2 IP first
2. Check port 80 is open in security group
3. Try manual installation:
   ```bash
   sudo certbot --nginx -d ocr.epingu.org --debug
   ```

### Can't Access UI

**Problem**: Browser can't reach `https://ocr.epingu.org`

**Solutions**:
1. Check security group allows ports 80 and 443 from 0.0.0.0/0
2. Verify Nginx is running: `sudo systemctl status nginx`
3. Check DNS with: `ping ocr.epingu.org`
4. Review Nginx logs: `sudo tail -f /var/log/nginx/error.log`

---

## 📈 Scaling Your Service

### Upgrade EC2 Instance

For higher traffic:

1. Stop instance
2. Change instance type (t3.medium → t3.large)
3. Start instance
4. Services auto-start

### Add Load Balancer

For very high traffic:

1. Create Application Load Balancer
2. Add EC2 instances as targets
3. Point ocr.epingu.org to ALB
4. Configure health checks

---

## ✅ Quick Command Reference

```bash
# Restart services
sudo systemctl restart aivision
sudo systemctl restart nginx

# View logs
sudo journalctl -u aivision -f
sudo tail -f /var/log/nginx/aivision_access.log

# Check status
sudo systemctl status aivision
sudo systemctl status nginx

# Test SSL
curl -I https://ocr.epingu.org/health

# Renew SSL
sudo certbot renew

# Backup database
sudo -u postgres pg_dump aivision > backup.sql
```

---

**🎉 Your AIVision OCR service is live at https://ocr.epingu.org!**

**Next Steps**:
1. Create your first template at `https://ocr.epingu.org/template-builder`
2. Test extraction at `https://ocr.epingu.org/simple-extract`
3. Share the URLs with your team
4. Monitor usage in logs
5. Scale as needed
