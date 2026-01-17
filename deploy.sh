#!/bin/bash
set -e

RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' BLUE='\033[0;34m' NC='\033[0m'
APP_DIR="/opt/aivision"

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step() { echo -e "\n${BLUE}[$1]${NC} $2"; }

kill_port() {
    local pids=$(lsof -ti :$1 2>/dev/null || true)
    [ -n "$pids" ] && echo "$pids" | xargs kill -9 2>/dev/null || true
}

wait_for_postgres() {
    warn "Waiting for PostgreSQL..."
    for i in $(seq 1 30); do
        sudo -u postgres psql -c "SELECT 1" &>/dev/null && log "PostgreSQL ready" && return 0
        sleep 1
    done
    sudo systemctl status postgresql@$PG_VERSION-main --no-pager || true
    err "PostgreSQL failed to start"
}

echo -e "${BLUE}"
cat << 'EOF'
    _    _____     ___     _
   / \  |_ _\ \   / (_)___(_) ___  _ __
  / _ \  | | \ \ / /| / __| |/ _ \| '_ \
 / ___ \ | |  \ V / | \__ \ | (_) | | | |
/_/   \_\___|  \_/  |_|___/_|\___/|_| |_|
EOF
echo -e "${NC}"

[ "$EUID" -eq 0 ] && err "Don't run as root"
[ ! -f /etc/os-release ] && err "Unsupported OS"

# 1. Configuration
step "1/8" "Configuration"
echo -e "\nAPI Keys (at least one required):"
read -p "  Gemini: " GEMINI_KEY
read -p "  OpenAI: " OPENAI_KEY
read -p "  Anthropic: " ANTHROPIC_KEY
[ -z "$GEMINI_KEY" ] && [ -z "$OPENAI_KEY" ] && [ -z "$ANTHROPIC_KEY" ] && err "Need at least one API key"

echo -e "\nDatabase (Enter for defaults):"
read -p "  Name [aivision]: " DB_NAME; DB_NAME=${DB_NAME:-aivision}
read -p "  User [aivision]: " DB_USER; DB_USER=${DB_USER:-aivision}
read -sp "  Password [auto]: " DB_PASS; echo
[ -z "$DB_PASS" ] && DB_PASS=$(openssl rand -hex 12) && log "Generated: $DB_PASS"

read -p "  Backend port [8000]: " BACKEND_PORT; BACKEND_PORT=${BACKEND_PORT:-8000}
read -p "  Frontend port [3000]: " FRONTEND_PORT; FRONTEND_PORT=${FRONTEND_PORT:-3000}
SECRET_KEY=$(openssl rand -hex 32)

# 2. Stop services
step "2/8" "Stopping services"
sudo systemctl stop aivision-backend nginx postgresql 2>/dev/null || true
kill_port $BACKEND_PORT; kill_port $FRONTEND_PORT; kill_port 5432
log "Services stopped"

# 3. Dependencies
step "3/8" "Installing dependencies"
sudo apt update -qq
sudo apt install -y -qq software-properties-common
apt-cache show python3.11 &>/dev/null || { warn "Adding deadsnakes PPA..."; sudo add-apt-repository -y ppa:deadsnakes/ppa; sudo apt update -qq; }
sudo apt install -y -qq python3.11 python3.11-venv python3.11-dev postgresql postgresql-contrib nginx curl build-essential libpq-dev poppler-utils tesseract-ocr lsof
command -v node &>/dev/null || { curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -; sudo apt install -y nodejs; }
log "Dependencies installed"

# 4. PostgreSQL
step "4/8" "PostgreSQL"
sudo rm -f /var/run/postgresql/.s.PGSQL.* /tmp/.s.PGSQL.* 2>/dev/null || true
PG_VERSION=$(psql --version 2>/dev/null | grep -oP '\d+' | head -1); [ -z "$PG_VERSION" ] && PG_VERSION="16"
warn "Creating PostgreSQL $PG_VERSION cluster on port 5432..."
sudo pg_dropcluster $PG_VERSION main --stop 2>/dev/null || true
sudo rm -rf /var/lib/postgresql/$PG_VERSION/main 2>/dev/null || true
sudo pg_createcluster $PG_VERSION main --port=5432
sudo systemctl daemon-reload
sudo systemctl enable --now postgresql@$PG_VERSION-main
wait_for_postgres
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME; DROP USER IF EXISTS $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS'; CREATE DATABASE $DB_NAME OWNER $DB_USER;"
log "PostgreSQL configured"

# 5. Application
step "5/8" "Application setup"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo mkdir -p $APP_DIR && sudo chown $USER:$USER $APP_DIR
[ "$SCRIPT_DIR" != "$APP_DIR" ] && cp -r "$SCRIPT_DIR"/* $APP_DIR/
cd $APP_DIR
cat > .env << EOF
ENVIRONMENT=production
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
SECRET_KEY=$SECRET_KEY
GOOGLE_API_KEY=$GEMINI_KEY
OPENAI_API_KEY=$OPENAI_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF
log "Config created"

# 6. Python
step "6/8" "Python setup"
python3.11 -m venv venv && source venv/bin/activate
pip install -q --upgrade pip && pip install -q -r requirements.txt
log "Python ready"

# 7. Frontend
step "7/8" "Frontend build"
cd $APP_DIR/frontend
echo "VITE_API_URL=http://localhost:$BACKEND_PORT" > .env
npm install --silent && npm run build --silent
log "Frontend built"

# 8. Services
step "8/8" "Starting services"
sudo tee /etc/systemd/system/aivision-backend.service > /dev/null << EOF
[Unit]
Description=AIVision Backend
After=network.target postgresql.service
[Service]
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$BACKEND_PORT
Restart=always
[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/nginx/sites-available/aivision > /dev/null << EOF
server {
    listen $FRONTEND_PORT;
    root $APP_DIR/frontend/dist;
    location / { try_files \$uri \$uri/ /index.html; }
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
    }
    location /health { proxy_pass http://127.0.0.1:$BACKEND_PORT/health; }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl enable --now aivision-backend
sudo systemctl restart nginx
log "Services started"

# Done
IP=$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_IP')
cat > $APP_DIR/CREDENTIALS.txt << EOF
AIVision - $(date)
Frontend: http://$IP:$FRONTEND_PORT
API Docs: http://$IP:$BACKEND_PORT/docs
Database: $DB_NAME / $DB_USER / $DB_PASS
EOF
chmod 600 $APP_DIR/CREDENTIALS.txt

echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}         INSTALLATION COMPLETE              ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "\n  Frontend:  ${BLUE}http://$IP:$FRONTEND_PORT${NC}"
echo -e "  API Docs:  ${BLUE}http://$IP:$BACKEND_PORT${NC}/docs"
echo -e "  Database:  $DB_NAME / $DB_USER / $DB_PASS"
echo -e "\n  Credentials: ${YELLOW}$APP_DIR/CREDENTIALS.txt${NC}"
echo -e "  Manage: ${BLUE}./scripts/manage.sh [start|stop|status|logs]${NC}\n"
