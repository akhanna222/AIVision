# AWS EC2 Deployment

## EC2 Instance

- **Type**: t3.medium (2 vCPU, 4GB RAM) minimum
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 30GB+ SSD

## Security Group

| Port | Description |
|------|-------------|
| 22 | SSH (restrict to your IP) |
| 80 | HTTP |
| 443 | HTTPS |

## Installation

```bash
# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Install dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-venv postgresql nginx git
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Setup PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE aivision;
CREATE USER aivision WITH PASSWORD 'CHANGE_THIS';
GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;
EOF

# Clone and configure
sudo mkdir -p /opt/aivision && sudo chown ubuntu:ubuntu /opt/aivision
cd /opt/aivision && git clone <repo-url> .
cp .env.example .env
nano .env  # Add credentials and API keys

# Deploy
chmod +x deploy/scripts/deploy.sh
sudo ./deploy/scripts/deploy.sh
```

## Environment Variables

```bash
DATABASE_URL=postgresql://aivision:password@localhost:5432/aivision
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key  # Optional
ANTHROPIC_API_KEY=your_key  # Optional
SECRET_KEY=$(openssl rand -hex 32)
```

## SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Management

```bash
# Services
sudo systemctl status aivision
sudo systemctl restart aivision

# Logs
sudo journalctl -u aivision -f
sudo tail -f /var/log/nginx/error.log

# Database
sudo -u postgres psql aivision
```

## Troubleshooting

```bash
# Check ports
sudo lsof -i :8000

# Test API
curl http://localhost:8000/health

# View errors
sudo journalctl -u aivision -n 50
```
