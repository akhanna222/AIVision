#!/bin/bash
#
# AIVision One-Command EC2 Deployment
# Usage: ./deploy.sh
#
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/aivision"

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step() { echo -e "\n${BLUE}[$1]${NC} $2"; }

# Kill process on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        warn "Killing process on port $port"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    local max_attempts=30
    local attempt=1
    warn "Waiting for PostgreSQL to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if sudo -u postgres psql -c "SELECT 1" &>/dev/null; then
            log "PostgreSQL is ready"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    # Show diagnostics on failure
    warn "PostgreSQL status:"
    sudo systemctl status postgresql --no-pager || true
    warn "PostgreSQL logs:"
    sudo journalctl -u postgresql --no-pager -n 20 || true
    err "PostgreSQL failed to start after ${max_attempts} seconds"
}

# Header
echo -e "${BLUE}"
cat << 'EOF'
    _    _____     ___     _
   / \  |_ _\ \   / (_)___(_) ___  _ __
  / _ \  | | \ \ / /| / __| |/ _ \| '_ \
 / ___ \ | |  \ V / | \__ \ | (_) | | | |
/_/   \_\___|  \_/  |_|___/_|\___/|_| |_|

         EC2 Deployment Script
EOF
echo -e "${NC}"

# Checks
[ "$EUID" -eq 0 ] && err "Don't run as root. Use: ./deploy.sh"
[ ! -f /etc/os-release ] && err "Unsupported OS"

# ============================================================================
# CONFIGURATION
# ============================================================================
step "1/8" "Collecting configuration"

echo ""
echo "API Keys (at least one required, Gemini is free):"
read -p "  Gemini API Key: " GEMINI_KEY
read -p "  OpenAI API Key: " OPENAI_KEY
read -p "  Anthropic API Key: " ANTHROPIC_KEY

[ -z "$GEMINI_KEY" ] && [ -z "$OPENAI_KEY" ] && [ -z "$ANTHROPIC_KEY" ] && \
    err "At least one API key required"

echo ""
echo "Database (press Enter for defaults):"
read -p "  Database name [aivision]: " DB_NAME && DB_NAME=${DB_NAME:-aivision}
read -p "  Database user [aivision]: " DB_USER && DB_USER=${DB_USER:-aivision}
read -sp "  Database password [auto]: " DB_PASS && echo ""
[ -z "$DB_PASS" ] && DB_PASS=$(openssl rand -hex 12) && log "Generated: $DB_PASS"

echo ""
echo "Ports:"
read -p "  Backend port [8000]: " BACKEND_PORT && BACKEND_PORT=${BACKEND_PORT:-8000}
read -p "  Frontend port [3000]: " FRONTEND_PORT && FRONTEND_PORT=${FRONTEND_PORT:-3000}

SECRET_KEY=$(openssl rand -hex 32)

# ============================================================================
# KILL EXISTING PROCESSES
# ============================================================================
step "2/8" "Clearing ports"

kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT
sudo systemctl stop aivision-backend 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true
sudo systemctl stop postgresql 2>/dev/null || true
kill_port 5432
log "Ports cleared"

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
step "3/8" "Installing dependencies"

sudo apt update -qq
sudo apt install -y -qq software-properties-common

# Add deadsnakes PPA for Python 3.11 (needed for Ubuntu < 23.04)
if ! apt-cache show python3.11 &>/dev/null; then
    warn "Adding deadsnakes PPA for Python 3.11..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update -qq
fi

sudo apt install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip \
    postgresql postgresql-contrib nginx git curl build-essential \
    libpq-dev poppler-utils tesseract-ocr lsof

if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi
log "Dependencies installed"

# ============================================================================
# POSTGRESQL
# ============================================================================
step "4/8" "Configuring PostgreSQL"

# Clean up stale socket files
sudo rm -f /var/run/postgresql/.s.PGSQL.* 2>/dev/null || true
sudo rm -f /tmp/.s.PGSQL.* 2>/dev/null || true

# Get PostgreSQL version
PG_VERSION=$(psql --version 2>/dev/null | grep -oP '\d+' | head -1)
[ -z "$PG_VERSION" ] && PG_VERSION="16"

# Always recreate cluster to avoid corruption issues
warn "Recreating PostgreSQL $PG_VERSION cluster..."
sudo systemctl stop postgresql@$PG_VERSION-main 2>/dev/null || true
sudo pg_dropcluster $PG_VERSION main --stop 2>/dev/null || true
sudo rm -rf /var/lib/postgresql/$PG_VERSION/main 2>/dev/null || true
sudo pg_createcluster $PG_VERSION main

# Start the versioned service
sudo systemctl daemon-reload
sudo systemctl enable postgresql@$PG_VERSION-main
sudo systemctl start postgresql@$PG_VERSION-main
wait_for_postgres

sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
log "PostgreSQL configured"

# ============================================================================
# APPLICATION SETUP
# ============================================================================
step "5/8" "Setting up application"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
[ "$SCRIPT_DIR" != "$APP_DIR" ] && cp -r "$SCRIPT_DIR"/* $APP_DIR/
cd $APP_DIR

# Environment file
cat > .env << EOF
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
SECRET_KEY=$SECRET_KEY
GOOGLE_API_KEY=$GEMINI_KEY
OPENAI_API_KEY=$OPENAI_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
ALLOWED_ORIGINS=["http://localhost:$FRONTEND_PORT","http://127.0.0.1:$FRONTEND_PORT"]
EOF
log "Configuration created"

# ============================================================================
# PYTHON SETUP
# ============================================================================
step "6/8" "Setting up Python"

python3.11 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
alembic upgrade head
log "Python environment ready"

# ============================================================================
# FRONTEND BUILD
# ============================================================================
step "7/8" "Building frontend"

cd $APP_DIR/frontend
echo "VITE_API_URL=http://localhost:$BACKEND_PORT" > .env
npm install --silent
npm run build --silent
log "Frontend built"

# ============================================================================
# SERVICES
# ============================================================================
step "8/8" "Creating services"

# Backend service
sudo tee /etc/systemd/system/aivision-backend.service > /dev/null << EOF
[Unit]
Description=AIVision Backend
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$BACKEND_PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Nginx
sudo tee /etc/nginx/sites-available/aivision > /dev/null << EOF
server {
    listen $FRONTEND_PORT;
    server_name _;
    root $APP_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
    }

    location /health {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/health;
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl enable aivision-backend
sudo systemctl start aivision-backend
sudo systemctl restart nginx
log "Services started"

# ============================================================================
# DONE
# ============================================================================
IP=$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_IP')

cat > $APP_DIR/CREDENTIALS.txt << EOF
AIVision Credentials - $(date)
==============================
Frontend: http://$IP:$FRONTEND_PORT
API Docs: http://$IP:$BACKEND_PORT/docs

Database: $DB_NAME / $DB_USER / $DB_PASS
Secret: $SECRET_KEY

Create account:
curl -X POST http://localhost:$BACKEND_PORT/api/v1/accounts -H "Content-Type: application/json" -d '{"name":"Admin","email":"admin@example.com"}'
EOF
chmod 600 $APP_DIR/CREDENTIALS.txt

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    INSTALLATION COMPLETE                    ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${BLUE}http://$IP:$FRONTEND_PORT${NC}"
echo -e "  API Docs:  ${BLUE}http://$IP:$BACKEND_PORT/docs${NC}"
echo ""
echo -e "  Database:  $DB_NAME / $DB_USER / $DB_PASS"
echo ""
echo -e "  Credentials saved to: ${YELLOW}$APP_DIR/CREDENTIALS.txt${NC}"
echo ""
echo -e "  Management: ${BLUE}./scripts/manage.sh [start|stop|logs|status]${NC}"
echo ""
