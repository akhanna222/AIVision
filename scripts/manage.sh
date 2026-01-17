#!/bin/bash
# AIVision Management Script
# Usage: ./scripts/manage.sh [command]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/opt/aivision"
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
DB_PORT=5432

# Load env if exists
[ -f "$APP_DIR/.env" ] && source "$APP_DIR/.env"

usage() {
    echo "AIVision Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show service status"
    echo "  logs        Show backend logs (live)"
    echo "  kill-ports  Kill processes on required ports"
    echo "  clean       Remove all data and reset"
    echo "  backup      Backup database"
    echo "  update      Pull latest code and restart"
    echo ""
}

kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Killing processes on port $port: $pids${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

cmd_kill_ports() {
    echo -e "${YELLOW}Killing processes on required ports...${NC}"
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    kill_port 5432  # PostgreSQL (be careful!)
    echo -e "${GREEN}✓ Ports cleared${NC}"
}

cmd_start() {
    echo -e "${GREEN}Starting AIVision services...${NC}"
    sudo systemctl start postgresql
    sudo systemctl start aivision-backend
    sudo systemctl start nginx
    echo -e "${GREEN}✓ Services started${NC}"
}

cmd_stop() {
    echo -e "${YELLOW}Stopping AIVision services...${NC}"
    sudo systemctl stop aivision-backend 2>/dev/null || true
    sudo systemctl stop nginx 2>/dev/null || true
    echo -e "${GREEN}✓ Services stopped${NC}"
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    echo -e "${GREEN}Service Status:${NC}"
    echo ""
    echo "Backend (aivision-backend):"
    systemctl is-active aivision-backend && echo -e "  ${GREEN}● Running${NC}" || echo -e "  ${RED}● Stopped${NC}"

    echo ""
    echo "Nginx:"
    systemctl is-active nginx && echo -e "  ${GREEN}● Running${NC}" || echo -e "  ${RED}● Stopped${NC}"

    echo ""
    echo "PostgreSQL:"
    systemctl is-active postgresql && echo -e "  ${GREEN}● Running${NC}" || echo -e "  ${RED}● Stopped${NC}"

    echo ""
    echo -e "${GREEN}Port Usage:${NC}"
    echo "  Backend ($BACKEND_PORT):  $(lsof -ti :$BACKEND_PORT 2>/dev/null && echo 'IN USE' || echo 'FREE')"
    echo "  Frontend ($FRONTEND_PORT): $(lsof -ti :$FRONTEND_PORT 2>/dev/null && echo 'IN USE' || echo 'FREE')"
}

cmd_logs() {
    sudo journalctl -u aivision-backend -f
}

cmd_clean() {
    echo -e "${RED}WARNING: This will delete all data!${NC}"
    read -p "Are you sure? (type 'yes' to confirm): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi

    cmd_stop
    cmd_kill_ports

    # Drop database
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS aivision;" 2>/dev/null || true

    # Remove app files
    sudo rm -rf $APP_DIR

    echo -e "${GREEN}✓ Cleaned${NC}"
}

cmd_backup() {
    local backup_file="aivision_backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${GREEN}Creating backup: $backup_file${NC}"

    # Get DB credentials from .env
    if [ -f "$APP_DIR/.env" ]; then
        source "$APP_DIR/.env"
        DB_URL=$DATABASE_URL
    fi

    sudo -u postgres pg_dump aivision > "$backup_file"
    echo -e "${GREEN}✓ Backup saved to $backup_file${NC}"
}

cmd_update() {
    echo -e "${GREEN}Updating AIVision...${NC}"
    cd $APP_DIR

    git pull

    source venv/bin/activate
    pip install -r requirements.txt
    alembic upgrade head

    cd frontend
    npm install
    npm run build

    cmd_restart
    echo -e "${GREEN}✓ Updated${NC}"
}

# Main
case "${1:-}" in
    start)      cmd_start ;;
    stop)       cmd_stop ;;
    restart)    cmd_restart ;;
    status)     cmd_status ;;
    logs)       cmd_logs ;;
    kill-ports) cmd_kill_ports ;;
    clean)      cmd_clean ;;
    backup)     cmd_backup ;;
    update)     cmd_update ;;
    *)          usage ;;
esac
