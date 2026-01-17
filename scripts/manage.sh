#!/bin/bash
set -e

RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' NC='\033[0m'
APP_DIR="/opt/aivision"
[ -f "$APP_DIR/.env" ] && source "$APP_DIR/.env"
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

kill_port() { lsof -ti :$1 2>/dev/null | xargs kill -9 2>/dev/null || true; }

status_check() {
    systemctl is-active $1 &>/dev/null && echo -e "${GREEN}● $1${NC}" || echo -e "${RED}○ $1${NC}"
}

case "${1:-help}" in
    start)
        sudo systemctl start postgresql aivision-backend nginx
        echo -e "${GREEN}✓ Started${NC}" ;;
    stop)
        sudo systemctl stop aivision-backend nginx 2>/dev/null || true
        echo -e "${GREEN}✓ Stopped${NC}" ;;
    restart)
        sudo systemctl restart postgresql aivision-backend nginx
        echo -e "${GREEN}✓ Restarted${NC}" ;;
    status)
        echo -e "${GREEN}Services:${NC}"
        status_check postgresql
        status_check aivision-backend
        status_check nginx
        echo -e "\n${GREEN}Ports:${NC}"
        echo "  $BACKEND_PORT: $(lsof -ti :$BACKEND_PORT &>/dev/null && echo 'used' || echo 'free')"
        echo "  $FRONTEND_PORT: $(lsof -ti :$FRONTEND_PORT &>/dev/null && echo 'used' || echo 'free')" ;;
    logs)
        sudo journalctl -u aivision-backend -f ;;
    kill-ports)
        kill_port $BACKEND_PORT; kill_port $FRONTEND_PORT; kill_port 5432
        echo -e "${GREEN}✓ Ports cleared${NC}" ;;
    clean)
        read -p "Delete all data? (yes): " c; [ "$c" != "yes" ] && exit 1
        sudo systemctl stop aivision-backend nginx 2>/dev/null || true
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS aivision;" 2>/dev/null || true
        sudo rm -rf $APP_DIR
        echo -e "${GREEN}✓ Cleaned${NC}" ;;
    backup)
        f="aivision_$(date +%Y%m%d_%H%M%S).sql"
        sudo -u postgres pg_dump aivision > "$f"
        echo -e "${GREEN}✓ Saved: $f${NC}" ;;
    update)
        cd $APP_DIR && git pull
        source venv/bin/activate && pip install -q -r requirements.txt && alembic upgrade head
        cd frontend && npm install --silent && npm run build --silent
        sudo systemctl restart aivision-backend nginx
        echo -e "${GREEN}✓ Updated${NC}" ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|kill-ports|clean|backup|update}" ;;
esac
