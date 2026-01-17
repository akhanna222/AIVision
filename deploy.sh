#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           AIVision OCR Service - EC2 Deployment           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please don't run as root. Run as regular user with sudo access.${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"

# ============================================================================
# COLLECT API KEYS
# ============================================================================
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                    API KEY CONFIGURATION                   ${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "At least ONE API key is required. Gemini offers a free tier."
echo ""

read -p "Enter Google Gemini API Key (free at aistudio.google.com) [optional]: " GEMINI_KEY
read -p "Enter OpenAI API Key [optional]: " OPENAI_KEY
read -p "Enter Anthropic API Key [optional]: " ANTHROPIC_KEY

if [ -z "$GEMINI_KEY" ] && [ -z "$OPENAI_KEY" ] && [ -z "$ANTHROPIC_KEY" ]; then
    echo -e "${RED}Error: At least one API key is required${NC}"
    exit 1
fi

# Database configuration
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                  DATABASE CONFIGURATION                    ${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

read -p "PostgreSQL database name [aivision]: " DB_NAME
DB_NAME=${DB_NAME:-aivision}

read -p "PostgreSQL username [aivision]: " DB_USER
DB_USER=${DB_USER:-aivision}

read -sp "PostgreSQL password [auto-generate]: " DB_PASS
echo ""
if [ -z "$DB_PASS" ]; then
    DB_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
    echo -e "${GREEN}Generated password: $DB_PASS${NC}"
fi

# Port configuration
echo ""
read -p "Backend port [8000]: " BACKEND_PORT
BACKEND_PORT=${BACKEND_PORT:-8000}

read -p "Frontend port [3000]: " FRONTEND_PORT
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

echo ""
echo -e "${GREEN}Configuration collected. Starting installation...${NC}"
echo ""

# ============================================================================
# INSTALL SYSTEM DEPENDENCIES
# ============================================================================
echo -e "${BLUE}[1/7] Installing system dependencies...${NC}"

sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr

# Install Node.js 18
if ! command -v node &> /dev/null; then
    echo -e "${BLUE}Installing Node.js 18...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo -e "${GREEN}✓ System dependencies installed${NC}"

# ============================================================================
# SETUP POSTGRESQL
# ============================================================================
echo -e "${BLUE}[2/7] Setting up PostgreSQL...${NC}"

sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo -e "${GREEN}✓ PostgreSQL configured${NC}"

# ============================================================================
# SETUP APPLICATION DIRECTORY
# ============================================================================
echo -e "${BLUE}[3/7] Setting up application...${NC}"

APP_DIR="/opt/aivision"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create app directory
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
if [ "$SCRIPT_DIR" != "$APP_DIR" ]; then
    cp -r "$SCRIPT_DIR"/* $APP_DIR/
fi

cd $APP_DIR

echo -e "${GREEN}✓ Application files copied to $APP_DIR${NC}"

# ============================================================================
# CREATE ENVIRONMENT FILE
# ============================================================================
echo -e "${BLUE}[4/7] Creating configuration...${NC}"

cat > $APP_DIR/.env << EOF
# AIVision Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME

# Security
SECRET_KEY=$SECRET_KEY

# API Keys
GOOGLE_API_KEY=$GEMINI_KEY
OPENAI_API_KEY=$OPENAI_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_KEY

# Server
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT

# CORS
ALLOWED_ORIGINS=["http://localhost:$FRONTEND_PORT","http://127.0.0.1:$FRONTEND_PORT"]
EOF

echo -e "${GREEN}✓ Configuration created${NC}"

# ============================================================================
# SETUP PYTHON ENVIRONMENT
# ============================================================================
echo -e "${BLUE}[5/7] Setting up Python environment...${NC}"

cd $APP_DIR

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

echo -e "${GREEN}✓ Python environment ready${NC}"

# ============================================================================
# SETUP FRONTEND
# ============================================================================
echo -e "${BLUE}[6/7] Building frontend...${NC}"

cd $APP_DIR/frontend

# Create frontend environment
cat > .env << EOF
VITE_API_URL=http://localhost:$BACKEND_PORT
EOF

npm install
npm run build

echo -e "${GREEN}✓ Frontend built${NC}"

# ============================================================================
# CREATE SYSTEMD SERVICES
# ============================================================================
echo -e "${BLUE}[7/7] Creating system services...${NC}"

# Backend service
sudo tee /etc/systemd/system/aivision-backend.service > /dev/null << EOF
[Unit]
Description=AIVision Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$BACKEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Frontend service (serves built files with nginx)
sudo tee /etc/nginx/sites-available/aivision > /dev/null << EOF
server {
    listen $FRONTEND_PORT;
    server_name _;

    root $APP_DIR/frontend/dist;
    index index.html;

    # Frontend routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/health;
    }
}
EOF

# Enable nginx site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/

# Reload services
sudo systemctl daemon-reload
sudo systemctl enable aivision-backend
sudo systemctl start aivision-backend
sudo systemctl restart nginx

echo -e "${GREEN}✓ Services configured and started${NC}"

# ============================================================================
# FINAL OUTPUT
# ============================================================================
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              INSTALLATION COMPLETE!                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Access your application:${NC}"
echo -e "  Frontend:  http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):$FRONTEND_PORT"
echo -e "  API Docs:  http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):$BACKEND_PORT/docs"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  Check status:    sudo systemctl status aivision-backend"
echo -e "  View logs:       sudo journalctl -u aivision-backend -f"
echo -e "  Restart:         sudo systemctl restart aivision-backend"
echo ""
echo -e "${BLUE}Database:${NC}"
echo -e "  Name:     $DB_NAME"
echo -e "  User:     $DB_USER"
echo -e "  Password: $DB_PASS"
echo ""
echo -e "${YELLOW}Save these credentials securely!${NC}"
echo ""

# Create a credentials file
cat > $APP_DIR/CREDENTIALS.txt << EOF
AIVision Installation Credentials
==================================
Generated: $(date)

Frontend URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):$FRONTEND_PORT
API URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):$BACKEND_PORT
API Docs: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):$BACKEND_PORT/docs

Database:
  Name: $DB_NAME
  User: $DB_USER
  Password: $DB_PASS

Secret Key: $SECRET_KEY

To create your first account, use the API:
curl -X POST http://localhost:$BACKEND_PORT/api/v1/accounts \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Your Name", "email": "your@email.com"}'
EOF

chmod 600 $APP_DIR/CREDENTIALS.txt
echo -e "${GREEN}Credentials saved to: $APP_DIR/CREDENTIALS.txt${NC}"
