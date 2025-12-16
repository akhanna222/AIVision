# 🔧 Running AIVision with Custom Ports (Alongside Other Apps)

Guide for deploying AIVision on an EC2 instance that already has apps running on ports 80, 443, 3000, and 8000.

---

## 📋 Your Current Port Usage

According to your security group:
- **Port 22** (SSH) - In use
- **Port 80** (HTTP) - In use by existing app
- **Port 443** (HTTPS) - In use by existing app
- **Port 3000** - In use by existing app
- **Port 8000** - In use by existing app

---

## 🎯 Three Deployment Options

### Option 1: Path-Based Routing (RECOMMENDED)
Use your existing Nginx on port 80/443, route AIVision to a subpath.

**URLs:**
```
Existing App:     http://your-ip/
AIVision:         http://your-ip/ocr/template-builder
                  http://your-ip/ocr/simple-extract
                  http://your-ip/ocr/docs
```

**Pros:** Clean, uses same domain/ports, professional URLs
**Cons:** Requires updating existing Nginx config

---

### Option 2: Different HTTP/HTTPS Ports
Run AIVision on non-standard ports (8080, 8443).

**URLs:**
```
Existing App:     http://your-ip/
AIVision:         http://your-ip:8080/template-builder
                  https://your-ip:8443/simple-extract
```

**Pros:** Completely separate, easy to set up
**Cons:** Users need to specify ports, not as clean

---

### Option 3: Subdomain Routing
Use subdomain with same Nginx instance.

**URLs:**
```
Existing App:     http://epingu.org/
AIVision:         http://ocr.epingu.org/template-builder
```

**Pros:** Most professional, separate domains
**Cons:** Requires DNS setup

---

## 🚀 OPTION 1: Path-Based Routing (RECOMMENDED)

This is the cleanest approach. All apps accessible from same domain/port.

### Step 1: Choose Backend Port for AIVision

Since 8000 is taken, use **8001**:

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Clone AIVision (if not already)
cd /opt
sudo mkdir aivision
sudo chown ubuntu:ubuntu aivision
cd aivision
git clone https://github.com/akhanna222/AIVision.git .
```

### Step 2: Create Environment File

```bash
nano /opt/aivision/.env
```

Paste this configuration (using port 8001):

```bash
# Database
DATABASE_URL=postgresql://aivision:CHANGE_THIS_PASSWORD@localhost:5432/aivision

# API Keys
GEMINI_API_KEY=AIzaSy_your_key_here
OPENAI_API_KEY=sk-your_key_optional
ANTHROPIC_API_KEY=sk-ant-your_key_optional

# Application
SECRET_KEY=$(openssl rand -base64 32)
APP_ENV=production
DEBUG=false
API_V1_PREFIX=/api/v1

# CORS - Allow all for public API
ALLOWED_ORIGINS=*

# Backend Port (CHANGED FROM 8000 TO 8001)
BACKEND_PORT=8001

# Storage - JSON only
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false
STORE_EXTRACTED_IMAGES=false

# Document Processing
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,tiff,heic

# Model Defaults
DEFAULT_VISION_MODEL=gemini-2.0-flash-exp
CONFIDENCE_THRESHOLD=0.80
```

### Step 3: Install Dependencies & Setup Database

```bash
cd /opt/aivision

# Create virtual environment
python3.11 -m venv venv

# Install dependencies
venv/bin/pip install -r requirements.txt

# Setup PostgreSQL database (if not exists)
sudo -u postgres psql <<EOF
CREATE DATABASE aivision;
CREATE USER aivision WITH ENCRYPTED PASSWORD 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;
\c aivision
GRANT ALL ON SCHEMA public TO aivision;
\q
EOF

# Run migrations
venv/bin/python -c "from app.db.session import init_db; init_db()"

# Build frontend
cd frontend
npm install

# Create production env pointing to /ocr subpath
cat > .env.production <<EOF
VITE_API_URL=/ocr
EOF

npm run build
cd ..
```

### Step 4: Create Systemd Service for AIVision Backend

```bash
sudo nano /etc/systemd/system/aivision.service
```

Paste this:

```ini
[Unit]
Description=AIVision OCR API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/aivision
Environment="PATH=/opt/aivision/venv/bin"
EnvironmentFile=/opt/aivision/.env
ExecStart=/opt/aivision/venv/bin/gunicorn -c /opt/aivision/gunicorn.conf.py app.main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 5: Create Gunicorn Config

```bash
nano /opt/aivision/gunicorn.conf.py
```

Paste this (binding to port 8001):

```python
import multiprocessing

# Server socket - USING PORT 8001
bind = "127.0.0.1:8001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
accesslog = "/var/log/aivision/access.log"
errorlog = "/var/log/aivision/error.log"
loglevel = "info"

# Process naming
proc_name = "aivision"
```

Create log directories:

```bash
sudo mkdir -p /var/log/aivision
sudo chown ubuntu:ubuntu /var/log/aivision
```

### Step 6: Start AIVision Backend

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aivision
sudo systemctl start aivision

# Check status
sudo systemctl status aivision

# Should show "active (running)"
```

### Step 7: Update Your Existing Nginx Config

Add AIVision routing to your existing Nginx configuration:

```bash
# Find your existing Nginx config
sudo nano /etc/nginx/sites-available/default
# Or wherever your current config is
```

Add this location block **inside your existing server block**:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Your existing app locations
    # ... existing config ...

    # AIVision Frontend - Serve from /ocr path
    location /ocr {
        alias /opt/aivision/frontend/dist;
        try_files $uri $uri/ /ocr/index.html;

        # Handle React Router
        location ~ ^/ocr/(?!api|health|docs|redoc|openapi.json).* {
            alias /opt/aivision/frontend/dist;
            try_files $uri /ocr/index.html;
        }
    }

    # AIVision API Backend
    location /ocr/api {
        proxy_pass http://127.0.0.1:8001/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # AIVision Health Check
    location /ocr/health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }

    # AIVision API Docs
    location /ocr/docs {
        proxy_pass http://127.0.0.1:8001/docs;
    }

    location /ocr/redoc {
        proxy_pass http://127.0.0.1:8001/redoc;
    }

    location /ocr/openapi.json {
        proxy_pass http://127.0.0.1:8001/openapi.json;
    }

    # Increase upload size for documents
    client_max_body_size 50M;
}
```

Test and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: Access AIVision

```
Template Builder:
http://your-ip/ocr/template-builder

Simple Extraction:
http://your-ip/ocr/simple-extract

API Docs:
http://your-ip/ocr/docs
```

---

## 🔌 OPTION 2: Different HTTP Ports

Run AIVision on ports 8080 (HTTP) and 8443 (HTTPS).

### Step 1: Update Security Group

Add these inbound rules:

| Type | Port | Source | Description |
|------|------|--------|-------------|
| Custom TCP | 8080 | 0.0.0.0/0 | AIVision HTTP |
| Custom TCP | 8443 | 0.0.0.0/0 | AIVision HTTPS |
| Custom TCP | 8001 | 0.0.0.0/0 | AIVision API (optional) |

### Step 2: Configure AIVision

Follow same steps as Option 1 for backend (port 8001).

### Step 3: Create Separate Nginx Config for AIVision

```bash
sudo nano /etc/nginx/sites-available/aivision
```

Paste this (using ports 8080/8443):

```nginx
# AIVision OCR - Separate Ports

upstream aivision_backend {
    server 127.0.0.1:8001 fail_timeout=0;
}

# HTTP on port 8080
server {
    listen 8080;
    server_name _;

    client_max_body_size 50M;

    # Frontend
    root /opt/aivision/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://aivision_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://aivision_backend/health;
        access_log off;
    }

    location /docs {
        proxy_pass http://aivision_backend/docs;
    }

    location /redoc {
        proxy_pass http://aivision_backend/redoc;
    }

    location /openapi.json {
        proxy_pass http://aivision_backend/openapi.json;
    }
}

# HTTPS on port 8443 (optional, requires SSL cert)
server {
    listen 8443 ssl;
    server_name _;

    # SSL certificates (you'll need to generate these)
    # ssl_certificate /etc/ssl/certs/aivision.crt;
    # ssl_certificate_key /etc/ssl/private/aivision.key;

    client_max_body_size 50M;

    # Same config as above
    root /opt/aivision/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://aivision_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Access AIVision

```
Template Builder:
http://your-ip:8080/template-builder

Simple Extraction:
http://your-ip:8080/simple-extract

API Docs:
http://your-ip:8080/docs
```

---

## 🌐 OPTION 3: Subdomain Routing

Best for epingu.org deployment with multiple services.

### Prerequisites

- Domain name (e.g., epingu.org)
- DNS access

### Step 1: Configure DNS

Add A record:

```
Type: A
Name: ocr
Value: YOUR_EC2_IP
TTL: 300
```

### Step 2: Update Nginx with Server Blocks

```bash
sudo nano /etc/nginx/sites-available/aivision
```

```nginx
# AIVision on ocr.epingu.org
upstream aivision_backend {
    server 127.0.0.1:8001 fail_timeout=0;
}

server {
    listen 80;
    server_name ocr.epingu.org;

    client_max_body_size 50M;

    root /opt/aivision/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://aivision_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://aivision_backend/health;
    }

    location /docs {
        proxy_pass http://aivision_backend/docs;
    }
}
```

### Step 3: Install SSL for Subdomain

```bash
sudo certbot --nginx -d ocr.epingu.org
```

### Step 4: Access AIVision

```
Template Builder:
https://ocr.epingu.org/template-builder

Simple Extraction:
https://ocr.epingu.org/simple-extract
```

---

## 🧪 Testing Your Setup

### Test Backend is Running

```bash
# Check service
sudo systemctl status aivision

# Test health endpoint
curl http://localhost:8001/health
# Should return: {"status":"healthy"}
```

### Test Frontend Access

**Option 1 (Path-based):**
```bash
curl -I http://localhost/ocr/template-builder
```

**Option 2 (Different port):**
```bash
curl -I http://localhost:8080/template-builder
```

**Option 3 (Subdomain):**
```bash
curl -I http://ocr.epingu.org/template-builder
```

All should return `HTTP 200 OK`.

---

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8001
sudo lsof -i :8001

# If needed, change to different port (8002, 8003, etc.)
nano /opt/aivision/.env
# Change BACKEND_PORT=8002

nano /opt/aivision/gunicorn.conf.py
# Change bind = "127.0.0.1:8002"

# Restart
sudo systemctl restart aivision
```

### Nginx Configuration Conflict

```bash
# Test Nginx config
sudo nginx -t

# View error details
sudo nginx -T

# Check if port 80 is available
sudo lsof -i :80
```

### Backend Not Starting

```bash
# View detailed logs
sudo journalctl -u aivision -n 50 --no-pager

# Check if database is accessible
sudo -u postgres psql aivision -c "SELECT 1;"

# Verify environment file
cat /opt/aivision/.env
```

---

## 📊 Port Summary

| Service | Default Port | Custom Port | Description |
|---------|--------------|-------------|-------------|
| Your Existing App | 80, 443 | - | HTTP/HTTPS |
| Your Existing App | 8000 | - | Backend API |
| Your Existing App | 3000 | - | Frontend Dev |
| **AIVision Backend** | 8000 | **8001** | FastAPI server |
| **AIVision HTTP (Option 2)** | 80 | **8080** | Nginx HTTP |
| **AIVision HTTPS (Option 2)** | 443 | **8443** | Nginx HTTPS |

---

## ✅ Recommended Setup for Your Case

Given your ports are occupied, I recommend:

**OPTION 1: Path-Based Routing**
- Backend: Port 8001
- Frontend: Served via existing Nginx at `/ocr/*`
- URLs: `http://your-ip/ocr/template-builder`
- **Cleanest solution, no new ports needed**

---

## 🆘 Quick Commands

```bash
# Restart AIVision backend
sudo systemctl restart aivision

# View AIVision logs
sudo journalctl -u aivision -f

# Check AIVision status
sudo systemctl status aivision

# Reload Nginx
sudo systemctl reload nginx

# Test Nginx config
sudo nginx -t
```

---

**Need help with the setup? Let me know which option you prefer!**
