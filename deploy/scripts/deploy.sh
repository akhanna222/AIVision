#!/bin/bash
###############################################################################
# AIVision OCR - AWS EC2 Deployment Script
#
# This script deploys the complete AIVision stack to an AWS EC2 instance:
# - PostgreSQL database (JSON storage only, NO file storage)
# - FastAPI backend with Gunicorn
# - React frontend (static build)
# - Nginx reverse proxy
# - SSL with Let's Encrypt (optional)
#
# Requirements:
# - Ubuntu 22.04 LTS EC2 instance
# - t3.medium or larger (2 vCPU, 4GB RAM minimum)
# - Security group with ports 22, 80, 443, 5432 open
# - Domain name (optional, for SSL)
#
# Usage:
#   sudo ./deploy.sh
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

###############################################################################
# Configuration
###############################################################################

# Get configuration from environment or use defaults
APP_USER="${APP_USER:-aivision}"
APP_DIR="${APP_DIR:-/opt/aivision}"
DB_NAME="${DB_NAME:-aivision}"
DB_USER="${DB_USER:-aivision}"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 32)}"
DOMAIN="${DOMAIN:-}"  # Optional: your-domain.com
EMAIL="${EMAIL:-admin@example.com}"

# API Keys (must be provided)
GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"

log_info "Starting AIVision deployment..."
log_info "App directory: $APP_DIR"
log_info "Database: $DB_NAME"

###############################################################################
# 1. System Updates and Dependencies
###############################################################################

log_info "Updating system packages..."
apt-get update
apt-get upgrade -y

log_info "Installing system dependencies..."
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    poppler-utils \
    libmagic1 \
    supervisor \
    certbot \
    python3-certbot-nginx \
    nodejs \
    npm

# Install Node.js 18
log_info "Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

###############################################################################
# 2. Create Application User
###############################################################################

log_info "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$APP_USER"
    log_info "User $APP_USER created"
else
    log_warn "User $APP_USER already exists"
fi

###############################################################################
# 3. Setup PostgreSQL Database (JSON STORAGE ONLY)
###############################################################################

log_info "Configuring PostgreSQL..."

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
-- Create database
CREATE DATABASE $DB_NAME;

-- Create user
CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to database and grant schema privileges
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;

-- Exit
\q
EOF

log_info "PostgreSQL database created: $DB_NAME"
log_info "Database user: $DB_USER"
log_info "Database password: $DB_PASSWORD"

# Save database credentials
cat > "$APP_DIR/.db_credentials" <<EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF

chmod 600 "$APP_DIR/.db_credentials"
chown "$APP_USER:$APP_USER" "$APP_DIR/.db_credentials"

###############################################################################
# 4. Clone Application Code
###############################################################################

log_info "Setting up application directory..."
mkdir -p "$APP_DIR"

# If code is already there, pull latest
if [ -d "$APP_DIR/.git" ]; then
    log_info "Pulling latest code..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull
else
    log_warn "Please manually copy your application code to $APP_DIR"
    log_warn "Or clone from your git repository"
fi

###############################################################################
# 5. Setup Python Backend
###############################################################################

log_info "Setting up Python backend..."

cd "$APP_DIR"

# Create virtual environment
sudo -u "$APP_USER" python3.11 -m venv venv

# Install Python dependencies
sudo -u "$APP_USER" venv/bin/pip install --upgrade pip
sudo -u "$APP_USER" venv/bin/pip install -r requirements.txt

# Create .env file
cat > "$APP_DIR/.env" <<EOF
# Database (JSON storage only - NO file storage)
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
REDIS_URL=redis://localhost:6379/0

# Vision Model API Keys
GOOGLE_API_KEY=$GOOGLE_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Application
SECRET_KEY=$(openssl rand -base64 32)
ENVIRONMENT=production
DEBUG=False
API_V1_PREFIX=/api/v1

# Storage Configuration - JSON ONLY IN DATABASE
STORAGE_TYPE=none  # Do not store files, only JSON in database
STORE_ORIGINAL_FILES=false
STORE_EXTRACTED_IMAGES=false

# CORS
ALLOWED_ORIGINS=http://localhost,https://$DOMAIN

# Document Processing
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,tiff,heic
PDF_DPI=300

# Model Defaults
DEFAULT_VISION_MODEL=gemini-2.0-flash-exp
CONFIDENCE_THRESHOLD=0.70
ENABLE_MODEL_FALLBACK=True

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
EOF

chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

# Run database migrations
log_info "Running database migrations..."
sudo -u "$APP_USER" venv/bin/python -c "from app.db.session import init_db; init_db()"

###############################################################################
# 6. Setup Frontend
###############################################################################

log_info "Building frontend..."

cd "$APP_DIR/frontend"

# Install dependencies
sudo -u "$APP_USER" npm install

# Create production .env
cat > "$APP_DIR/frontend/.env.production" <<EOF
VITE_API_URL=https://$DOMAIN
EOF

# Build frontend
sudo -u "$APP_USER" npm run build

log_info "Frontend built successfully"

###############################################################################
# 7. Setup Gunicorn (Backend Service)
###############################################################################

log_info "Configuring Gunicorn..."

# Create Gunicorn config
cat > "$APP_DIR/gunicorn.conf.py" <<EOF
# Gunicorn configuration for AIVision backend
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
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

# Server mechanics
daemon = False
pidfile = "/var/run/aivision/gunicorn.pid"
user = "$APP_USER"
group = "$APP_USER"

# SSL (if needed)
# keyfile = "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
# certfile = "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
EOF

# Create log directories
mkdir -p /var/log/aivision
mkdir -p /var/run/aivision
chown -R "$APP_USER:$APP_USER" /var/log/aivision
chown -R "$APP_USER:$APP_USER" /var/run/aivision

###############################################################################
# 8. Setup Systemd Service
###############################################################################

log_info "Creating systemd service..."

cat > /etc/systemd/system/aivision.service <<EOF
[Unit]
Description=AIVision OCR API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn -c $APP_DIR/gunicorn.conf.py app.main:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aivision
systemctl start aivision

log_info "AIVision service started"

###############################################################################
# 9. Setup Nginx
###############################################################################

log_info "Configuring Nginx..."

cat > /etc/nginx/sites-available/aivision <<EOF
# AIVision OCR - Nginx Configuration

upstream aivision_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name $DOMAIN ${DOMAIN:-localhost};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size (50MB)
    client_max_body_size 50M;

    # Frontend (React build)
    root $APP_DIR/frontend/dist;
    index index.html;

    # Frontend routes (SPA)
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API backend
    location /api {
        proxy_pass http://aivision_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts for long-running extractions
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://aivision_backend/health;
        access_log off;
    }

    # API documentation
    location /docs {
        proxy_pass http://aivision_backend/docs;
    }

    location /redoc {
        proxy_pass http://aivision_backend/redoc;
    }

    location /openapi.json {
        proxy_pass http://aivision_backend/openapi.json;
    }

    # Logging
    access_log /var/log/nginx/aivision_access.log;
    error_log /var/log/nginx/aivision_error.log;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Restart nginx
systemctl restart nginx
systemctl enable nginx

log_info "Nginx configured successfully"

###############################################################################
# 10. Setup SSL (Optional)
###############################################################################

if [ -n "$DOMAIN" ]; then
    log_info "Setting up SSL with Let's Encrypt..."

    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

    log_info "SSL certificate installed"
else
    log_warn "No domain provided, skipping SSL setup"
    log_warn "To add SSL later, run: certbot --nginx -d your-domain.com"
fi

###############################################################################
# 11. Setup Firewall
###############################################################################

log_info "Configuring firewall..."

ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

log_info "Firewall configured"

###############################################################################
# 12. Final Steps
###############################################################################

log_info "Deployment completed successfully!"
log_info ""
log_info "=========================================="
log_info "AIVision OCR Deployment Summary"
log_info "=========================================="
log_info "Application Directory: $APP_DIR"
log_info "Database: PostgreSQL (JSON storage only)"
log_info "  - Database: $DB_NAME"
log_info "  - User: $DB_USER"
log_info "  - Password: $DB_PASSWORD"
log_info ""
log_info "Services:"
log_info "  - Backend: systemctl status aivision"
log_info "  - Database: systemctl status postgresql"
log_info "  - Webserver: systemctl status nginx"
log_info ""
log_info "URLs:"
if [ -n "$DOMAIN" ]; then
    log_info "  - Frontend: https://$DOMAIN"
    log_info "  - API Docs: https://$DOMAIN/docs"
    log_info "  - Health: https://$DOMAIN/health"
else
    log_info "  - Frontend: http://$(curl -s ifconfig.me)"
    log_info "  - API Docs: http://$(curl -s ifconfig.me)/docs"
fi
log_info ""
log_info "Logs:"
log_info "  - Backend: /var/log/aivision/"
log_info "  - Nginx: /var/log/nginx/"
log_info "  - Systemd: journalctl -u aivision -f"
log_info ""
log_info "Next Steps:"
log_info "1. Create your first account:"
log_info "   curl -X POST http://localhost/api/v1/accounts \\"
log_info "     -H 'Content-Type: application/json' \\"
log_info "     -d '{\"name\":\"Test\",\"email\":\"test@test.com\",\"plan\":\"professional\"}'"
log_info ""
log_info "2. Save your API token from the response"
log_info ""
log_info "3. Test extraction:"
log_info "   curl -X POST http://localhost/api/v1/extractions/extract \\"
log_info "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
log_info "     -F 'file=@document.pdf'"
log_info ""
log_info "=========================================="
log_info "Storage Configuration: JSON ONLY in PostgreSQL"
log_info "Original files are NOT stored (deleted after processing)"
log_info "=========================================="

# Save deployment info
cat > "$APP_DIR/deployment_info.txt" <<EOF
AIVision Deployment Information
Generated: $(date)

Database:
  Host: localhost
  Port: 5432
  Database: $DB_NAME
  User: $DB_USER
  Password: $DB_PASSWORD

Services:
  Backend: systemctl status aivision
  Database: systemctl status postgresql
  Webserver: systemctl status nginx

Logs:
  Backend: /var/log/aivision/
  Nginx: /var/log/nginx/
  Systemd: journalctl -u aivision -f

Storage:
  Type: Database only (JSON)
  Original files: NOT stored
  Extraction results: PostgreSQL JSON columns
EOF

chown "$APP_USER:$APP_USER" "$APP_DIR/deployment_info.txt"

log_info "Deployment info saved to: $APP_DIR/deployment_info.txt"
