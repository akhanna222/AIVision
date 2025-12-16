#!/bin/bash
###############################################################################
# AIVision OCR - Interactive Installation Script
#
# This script guides you through the complete installation of AIVision
# on your EC2 instance with interactive prompts and automatic configuration.
#
# Usage:
#   curl -o install.sh https://raw.githubusercontent.com/akhanna222/AIVision/claude/ocr-service-templates-01MnNQz5UdYNuAmnsHtobQtM/install.sh
#   chmod +x install.sh
#   sudo ./install.sh
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

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

log_step() {
    echo -e "\n${CYAN}${BOLD}==>${NC} ${BOLD}$1${NC}\n"
}

log_success() {
    echo -e "${GREEN}${BOLD}✓${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}

###############################################################################
# Welcome Screen
###############################################################################

clear
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║              🚀 AIVision OCR Interactive Installer 🚀                ║
║                                                                       ║
║           Welcome! This installer will guide you through             ║
║           setting up AIVision OCR service on your server.            ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF

echo ""
log_info "This installer will:"
echo "  1. Check your system requirements"
echo "  2. Detect port conflicts"
echo "  3. Configure deployment options"
echo "  4. Install all dependencies"
echo "  5. Setup database and services"
echo "  6. Configure web server"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."

###############################################################################
# Step 1: System Check
###############################################################################

log_step "Step 1: Checking System Requirements"

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    log_info "OS: $NAME $VERSION"
else
    log_error "Cannot detect OS"
    exit 1
fi

# Check Python
log_info "Checking Python installation..."
PYTHON_CMD=""
for py in python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v $py &> /dev/null; then
        PYTHON_VERSION=$($py --version 2>&1 | awk '{print $2}')
        log_success "Found: $py (version $PYTHON_VERSION)"
        PYTHON_CMD=$py
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    log_error "Python 3.8+ not found. Installing Python 3..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
    PYTHON_CMD=python3
fi

# Check Node.js
log_info "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_success "Found: Node.js $NODE_VERSION"
else
    log_warn "Node.js not found. Will install later."
fi

# Check available memory
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
log_info "Available RAM: ${TOTAL_MEM}MB"
if [ $TOTAL_MEM -lt 2000 ]; then
    log_warn "Less than 2GB RAM detected. Performance may be limited."
fi

###############################################################################
# Step 2: Port Detection
###############################################################################

log_step "Step 2: Detecting Port Usage"

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port available
    fi
}

# Check common ports
PORT_80_IN_USE=false
PORT_443_IN_USE=false
PORT_8000_IN_USE=false
PORT_3000_IN_USE=false

if check_port 80; then
    log_warn "Port 80 is in use"
    PORT_80_IN_USE=true
else
    log_success "Port 80 is available"
fi

if check_port 443; then
    log_warn "Port 443 is in use"
    PORT_443_IN_USE=true
else
    log_success "Port 443 is available"
fi

if check_port 8000; then
    log_warn "Port 8000 is in use"
    PORT_8000_IN_USE=true
else
    log_success "Port 8000 is available"
fi

if check_port 3000; then
    log_warn "Port 3000 is in use"
    PORT_3000_IN_USE=true
else
    log_success "Port 3000 is available"
fi

###############################################################################
# Step 3: Deployment Configuration
###############################################################################

log_step "Step 3: Deployment Configuration"

# Determine backend port
if [ "$PORT_8000_IN_USE" = true ]; then
    log_warn "Port 8000 is occupied. Finding alternative..."
    BACKEND_PORT=8001
    while check_port $BACKEND_PORT; do
        BACKEND_PORT=$((BACKEND_PORT + 1))
    done
    log_info "Will use port $BACKEND_PORT for backend"
else
    BACKEND_PORT=8000
    log_info "Will use port 8000 for backend"
fi

# Choose deployment mode
echo ""
echo -e "${BOLD}Choose deployment mode:${NC}"
echo ""

if [ "$PORT_80_IN_USE" = true ] || [ "$PORT_443_IN_USE" = true ]; then
    log_warn "Ports 80/443 are in use. You have these options:"
    echo ""
    echo "  1) Path-based routing    - Add /ocr/* routes to existing Nginx"
    echo "                             URLs: http://your-ip/ocr/template-builder"
    echo ""
    echo "  2) Different ports       - Run on ports 8080/8443"
    echo "                             URLs: http://your-ip:8080/template-builder"
    echo ""
    echo "  3) Subdomain             - Use ocr.epingu.org (requires DNS)"
    echo "                             URLs: https://ocr.epingu.org/template-builder"
    echo ""
    read -p "Enter your choice (1-3) [default: 1]: " DEPLOY_MODE
    DEPLOY_MODE=${DEPLOY_MODE:-1}
else
    echo "  1) Standard deployment   - Use ports 80/443 directly"
    echo "                             URLs: http://your-ip/template-builder"
    echo ""
    echo "  2) Subdomain             - Use ocr.epingu.org (requires DNS)"
    echo "                             URLs: https://ocr.epingu.org/template-builder"
    echo ""
    read -p "Enter your choice (1-2) [default: 1]: " DEPLOY_MODE
    DEPLOY_MODE=${DEPLOY_MODE:-1}
fi

# Domain configuration
DOMAIN=""
USE_SSL=false
if [ "$DEPLOY_MODE" = "2" ] && [ "$PORT_80_IN_USE" = false ]; then
    # Subdomain with standard ports
    read -p "Enter your domain (e.g., ocr.epingu.org) or leave empty: " DOMAIN
    if [ -n "$DOMAIN" ]; then
        read -p "Install SSL certificate with Let's Encrypt? (y/n) [default: y]: " INSTALL_SSL
        INSTALL_SSL=${INSTALL_SSL:-y}
        if [[ $INSTALL_SSL =~ ^[Yy]$ ]]; then
            USE_SSL=true
            read -p "Enter your email for SSL certificate: " SSL_EMAIL
        fi
    fi
elif [ "$DEPLOY_MODE" = "3" ]; then
    # Subdomain with custom ports
    read -p "Enter your domain (e.g., ocr.epingu.org) or leave empty: " DOMAIN
    if [ -n "$DOMAIN" ]; then
        read -p "Install SSL certificate with Let's Encrypt? (y/n) [default: y]: " INSTALL_SSL
        INSTALL_SSL=${INSTALL_SSL:-y}
        if [[ $INSTALL_SSL =~ ^[Yy]$ ]]; then
            USE_SSL=true
            read -p "Enter your email for SSL certificate: " SSL_EMAIL
        fi
    fi
fi

###############################################################################
# Step 4: API Keys Configuration
###############################################################################

log_step "Step 4: API Keys Configuration"

echo ""
log_info "You need at least ONE API key. Gemini is FREE (60 requests/min)!"
echo ""
echo "Get API keys from:"
echo "  • Gemini (FREE):     https://makersuite.google.com/app/apikey"
echo "  • OpenAI (Paid):     https://platform.openai.com/api-keys"
echo "  • Anthropic (Paid):  https://console.anthropic.com/"
echo ""

read -p "Enter Gemini API key (or leave empty): " GEMINI_API_KEY
read -p "Enter OpenAI API key (optional): " OPENAI_API_KEY
read -p "Enter Anthropic API key (optional): " ANTHROPIC_API_KEY

if [ -z "$GEMINI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    log_error "At least one API key is required!"
    exit 1
fi

###############################################################################
# Step 5: Installation Directory
###############################################################################

log_step "Step 5: Installation Directory"

read -p "Installation directory [default: /opt/aivision]: " APP_DIR
APP_DIR=${APP_DIR:-/opt/aivision}

if [ -d "$APP_DIR" ]; then
    log_warn "Directory $APP_DIR already exists"
    read -p "Continue and overwrite? (y/n): " OVERWRITE
    if [[ ! $OVERWRITE =~ ^[Yy]$ ]]; then
        log_error "Installation cancelled"
        exit 1
    fi
fi

###############################################################################
# Step 6: Database Configuration
###############################################################################

log_step "Step 6: Database Configuration"

DB_NAME="aivision"
DB_USER="aivision"
DB_PASSWORD=$(openssl rand -base64 32)

read -p "PostgreSQL database name [default: aivision]: " INPUT_DB_NAME
DB_NAME=${INPUT_DB_NAME:-$DB_NAME}

read -p "PostgreSQL user [default: aivision]: " INPUT_DB_USER
DB_USER=${INPUT_DB_USER:-$DB_USER}

read -p "Generate random PostgreSQL password? (y/n) [default: y]: " GEN_PASSWORD
GEN_PASSWORD=${GEN_PASSWORD:-y}
if [[ ! $GEN_PASSWORD =~ ^[Yy]$ ]]; then
    read -sp "Enter PostgreSQL password: " DB_PASSWORD
    echo ""
fi

###############################################################################
# Summary
###############################################################################

log_step "Configuration Summary"

echo ""
echo -e "${BOLD}Deployment Configuration:${NC}"
echo "  Installation Directory: $APP_DIR"
echo "  Python Command: $PYTHON_CMD"
echo "  Backend Port: $BACKEND_PORT"

case $DEPLOY_MODE in
    1)
        if [ "$PORT_80_IN_USE" = true ]; then
            echo "  Deployment Mode: Path-based routing (/ocr/*)"
            echo "  Web Ports: Using existing Nginx on 80/443"
        else
            echo "  Deployment Mode: Standard (direct ports)"
            echo "  Web Ports: 80 (HTTP), 443 (HTTPS)"
        fi
        ;;
    2)
        if [ "$PORT_80_IN_USE" = true ]; then
            echo "  Deployment Mode: Custom ports"
            echo "  Web Ports: 8080 (HTTP), 8443 (HTTPS)"
        else
            echo "  Deployment Mode: Subdomain"
            echo "  Domain: $DOMAIN"
            echo "  Web Ports: 80 (HTTP), 443 (HTTPS)"
        fi
        ;;
    3)
        echo "  Deployment Mode: Subdomain with custom ports"
        echo "  Domain: $DOMAIN"
        echo "  Web Ports: 8080 (HTTP), 8443 (HTTPS)"
        ;;
esac

echo ""
echo -e "${BOLD}Database Configuration:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: ${DB_PASSWORD:0:10}... (saved to $APP_DIR/.db_credentials)"

echo ""
echo -e "${BOLD}API Keys:${NC}"
[ -n "$GEMINI_API_KEY" ] && echo "  ✓ Gemini API configured"
[ -n "$OPENAI_API_KEY" ] && echo "  ✓ OpenAI API configured"
[ -n "$ANTHROPIC_API_KEY" ] && echo "  ✓ Anthropic API configured"

echo ""
read -p "Proceed with installation? (y/n): " PROCEED
if [[ ! $PROCEED =~ ^[Yy]$ ]]; then
    log_error "Installation cancelled"
    exit 1
fi

###############################################################################
# Installation Start
###############################################################################

log_step "Starting Installation"

# Update system
log_info "Updating system packages..."
apt-get update -qq

###############################################################################
# Install Dependencies
###############################################################################

log_step "Installing Dependencies"

log_info "Installing system packages..."
apt-get install -y -qq \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    lsof \
    net-tools \
    build-essential \
    libpq-dev \
    poppler-utils \
    libmagic1 \
    certbot \
    python3-certbot-nginx \
    python3-pip \
    python3-venv

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    log_info "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
    apt-get install -y nodejs
fi

log_success "Dependencies installed"

###############################################################################
# Clone Repository
###############################################################################

log_step "Downloading AIVision"

mkdir -p $APP_DIR
cd $APP_DIR

if [ -d ".git" ]; then
    log_info "Updating existing repository..."
    sudo -u $ACTUAL_USER git pull
else
    log_info "Cloning repository..."
    sudo -u $ACTUAL_USER git clone -b claude/ocr-service-templates-01MnNQz5UdYNuAmnsHtobQtM \
        https://github.com/akhanna222/AIVision.git .
fi

log_success "Code downloaded"

###############################################################################
# Setup PostgreSQL
###############################################################################

log_step "Setting up PostgreSQL Database"

systemctl start postgresql
systemctl enable postgresql

log_info "Creating database and user..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null || true

sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

# Save credentials
cat > "$APP_DIR/.db_credentials" <<EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
chmod 600 "$APP_DIR/.db_credentials"

log_success "Database created: $DB_NAME"

###############################################################################
# Setup Python Backend
###############################################################################

log_step "Setting up Python Backend"

log_info "Creating virtual environment..."
sudo -u $ACTUAL_USER $PYTHON_CMD -m venv venv

log_info "Installing Python packages..."
sudo -u $ACTUAL_USER venv/bin/pip install --upgrade pip -q
sudo -u $ACTUAL_USER venv/bin/pip install -r requirements.txt -q

log_success "Python environment ready"

###############################################################################
# Create Environment File
###############################################################################

log_step "Creating Environment Configuration"

SECRET_KEY=$(openssl rand -base64 32)

cat > "$APP_DIR/.env" <<EOF
# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME

# API Keys
GEMINI_API_KEY=$GEMINI_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Application
SECRET_KEY=$SECRET_KEY
APP_ENV=production
DEBUG=false
API_V1_PREFIX=/api/v1

# CORS - Allow all for public API
ALLOWED_ORIGINS=*

# Backend Port
BACKEND_PORT=$BACKEND_PORT

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
EOF

chmod 600 "$APP_DIR/.env"
chown $ACTUAL_USER:$ACTUAL_USER "$APP_DIR/.env"

log_success "Environment configured"

###############################################################################
# Run Database Migrations
###############################################################################

log_step "Running Database Migrations"

sudo -u $ACTUAL_USER venv/bin/python -c "from app.db.session import init_db; init_db()"

log_success "Database migrations complete"

###############################################################################
# Build Frontend
###############################################################################

log_step "Building Frontend"

cd frontend

log_info "Installing npm packages..."
sudo -u $ACTUAL_USER npm install -q

# Create production environment
if [ "$DEPLOY_MODE" = "1" ] && [ "$PORT_80_IN_USE" = true ]; then
    # Path-based routing
    cat > .env.production <<EOF
VITE_API_URL=/ocr
EOF
else
    # Standard routing
    cat > .env.production <<EOF
VITE_API_URL=
EOF
fi

log_info "Building React app..."
sudo -u $ACTUAL_USER npm run build

cd ..

log_success "Frontend built"

###############################################################################
# Setup Gunicorn
###############################################################################

log_step "Configuring Application Server"

cat > "$APP_DIR/gunicorn.conf.py" <<EOF
import multiprocessing

bind = "127.0.0.1:$BACKEND_PORT"
backlog = 2048

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 300
keepalive = 2

accesslog = "/var/log/aivision/access.log"
errorlog = "/var/log/aivision/error.log"
loglevel = "info"

proc_name = "aivision"
EOF

mkdir -p /var/log/aivision
chown $ACTUAL_USER:$ACTUAL_USER /var/log/aivision

log_success "Application server configured"

###############################################################################
# Setup Systemd Service
###############################################################################

log_step "Creating System Service"

cat > /etc/systemd/system/aivision.service <<EOF
[Unit]
Description=AIVision OCR API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn -c $APP_DIR/gunicorn.conf.py app.main:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aivision
systemctl start aivision

log_success "Service started"

###############################################################################
# Configure Nginx
###############################################################################

log_step "Configuring Web Server"

if [ "$DEPLOY_MODE" = "1" ] && [ "$PORT_80_IN_USE" = true ]; then
    # Path-based routing - add to existing config
    log_warn "Path-based routing selected"
    log_warn "You need to manually add the following to your existing Nginx config:"
    echo ""
    cat <<'EOF'
    location /ocr {
        alias /opt/aivision/frontend/dist;
        index index.html;
        try_files $uri $uri/ /ocr/index.html;
    }

    location /ocr/api {
        proxy_pass http://127.0.0.1:8001/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /ocr/health {
        proxy_pass http://127.0.0.1:8001/health;
    }

    location /ocr/docs {
        proxy_pass http://127.0.0.1:8001/docs;
    }

    client_max_body_size 50M;
EOF
    echo ""
    read -p "Press Enter after you've added this to your Nginx config..."
    nginx -t && systemctl reload nginx

elif [ "$DEPLOY_MODE" = "2" ] && [ "$PORT_80_IN_USE" = true ]; then
    # Different ports
    HTTP_PORT=8080
    HTTPS_PORT=8443

    cat > /etc/nginx/sites-available/aivision <<EOF
upstream aivision_backend {
    server 127.0.0.1:$BACKEND_PORT fail_timeout=0;
}

server {
    listen $HTTP_PORT;
    server_name ${DOMAIN:-_};

    client_max_body_size 50M;

    root $APP_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://aivision_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://aivision_backend/health;
    }

    location /docs {
        proxy_pass http://aivision_backend/docs;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx

    log_info "AIVision accessible on port $HTTP_PORT"

else
    # Standard deployment
    cat > /etc/nginx/sites-available/aivision <<EOF
upstream aivision_backend {
    server 127.0.0.1:$BACKEND_PORT fail_timeout=0;
}

server {
    listen 80;
    server_name ${DOMAIN:-_};

    client_max_body_size 50M;

    root $APP_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://aivision_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://aivision_backend/health;
        access_log off;
    }

    location /docs {
        proxy_pass http://aivision_backend/docs;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/aivision /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
fi

log_success "Web server configured"

###############################################################################
# SSL Certificate
###############################################################################

if [ "$USE_SSL" = true ] && [ -n "$DOMAIN" ]; then
    log_step "Installing SSL Certificate"

    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$SSL_EMAIL" --redirect || {
        log_warn "SSL certificate installation failed. You can install it later with:"
        echo "  sudo certbot --nginx -d $DOMAIN"
    }
fi

###############################################################################
# Firewall Configuration
###############################################################################

log_step "Configuring Firewall"

if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow 22/tcp   # SSH

    if [ "$DEPLOY_MODE" = "2" ] && [ "$PORT_80_IN_USE" = true ]; then
        ufw allow 8080/tcp
        ufw allow 8443/tcp
    else
        ufw allow 80/tcp
        ufw allow 443/tcp
    fi

    log_success "Firewall configured"
fi

###############################################################################
# Installation Complete
###############################################################################

clear
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           ✅ Installation Complete! ✅                                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF

echo ""
log_success "AIVision OCR is now installed and running!"
echo ""

# Display access URLs
echo -e "${BOLD}Access Your AIVision Installation:${NC}"
echo ""

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

if [ "$DEPLOY_MODE" = "1" ] && [ "$PORT_80_IN_USE" = true ]; then
    echo "  Template Builder:  http://$SERVER_IP/ocr/template-builder"
    echo "  Simple Extraction: http://$SERVER_IP/ocr/simple-extract"
    echo "  API Docs:          http://$SERVER_IP/ocr/docs"
elif [ "$DEPLOY_MODE" = "2" ] && [ "$PORT_80_IN_USE" = true ]; then
    echo "  Template Builder:  http://$SERVER_IP:8080/template-builder"
    echo "  Simple Extraction: http://$SERVER_IP:8080/simple-extract"
    echo "  API Docs:          http://$SERVER_IP:8080/docs"
elif [ -n "$DOMAIN" ]; then
    if [ "$USE_SSL" = true ]; then
        echo "  Template Builder:  https://$DOMAIN/template-builder"
        echo "  Simple Extraction: https://$DOMAIN/simple-extract"
        echo "  API Docs:          https://$DOMAIN/docs"
    else
        echo "  Template Builder:  http://$DOMAIN/template-builder"
        echo "  Simple Extraction: http://$DOMAIN/simple-extract"
        echo "  API Docs:          http://$DOMAIN/docs"
    fi
else
    echo "  Template Builder:  http://$SERVER_IP/template-builder"
    echo "  Simple Extraction: http://$SERVER_IP/simple-extract"
    echo "  API Docs:          http://$SERVER_IP/docs"
fi

echo ""
echo -e "${BOLD}Service Management:${NC}"
echo "  Check status:   sudo systemctl status aivision"
echo "  View logs:      sudo journalctl -u aivision -f"
echo "  Restart:        sudo systemctl restart aivision"
echo ""

echo -e "${BOLD}Important Files:${NC}"
echo "  Installation:   $APP_DIR"
echo "  Environment:    $APP_DIR/.env"
echo "  DB Credentials: $APP_DIR/.db_credentials"
echo "  Logs:           /var/log/aivision/"
echo ""

echo -e "${BOLD}Next Steps:${NC}"
echo "  1. Open the Template Builder URL in your browser"
echo "  2. Create your first template"
echo "  3. Test extraction with the Simple Extraction UI"
echo ""

if [ "$DEPLOY_MODE" = "1" ] && [ "$PORT_80_IN_USE" = true ]; then
    log_warn "Don't forget to reload your Nginx after adding the /ocr routes!"
fi

echo ""
log_info "For documentation, see: $APP_DIR/*.md"
echo ""

# Save installation summary
cat > "$APP_DIR/installation_summary.txt" <<EOF
AIVision Installation Summary
Generated: $(date)

Server IP: $SERVER_IP
Installation Directory: $APP_DIR
Backend Port: $BACKEND_PORT

Access URLs:
$(if [ "$DEPLOY_MODE" = "1" ] && [ "$PORT_80_IN_USE" = true ]; then
    echo "  http://$SERVER_IP/ocr/template-builder"
elif [ "$DEPLOY_MODE" = "2" ] && [ "$PORT_80_IN_USE" = true ]; then
    echo "  http://$SERVER_IP:8080/template-builder"
elif [ -n "$DOMAIN" ]; then
    echo "  https://$DOMAIN/template-builder"
else
    echo "  http://$SERVER_IP/template-builder"
fi)

Database:
  Name: $DB_NAME
  User: $DB_USER
  Credentials: $APP_DIR/.db_credentials

Services:
  sudo systemctl status aivision
  sudo journalctl -u aivision -f

Configuration:
  Environment: $APP_DIR/.env
  Nginx: /etc/nginx/sites-available/aivision
EOF

log_success "Installation summary saved to: $APP_DIR/installation_summary.txt"

echo ""
read -p "Press Enter to exit..."
