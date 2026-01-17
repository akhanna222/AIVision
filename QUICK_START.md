# Quick Start - EC2 Installation

## One-Command Install

```bash
curl -o install.sh https://raw.githubusercontent.com/akhanna222/AIVision/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

The installer will:
1. Detect system requirements and port conflicts
2. Ask for API keys and configuration
3. Install dependencies (PostgreSQL, Nginx, Python, Node.js)
4. Setup database and services
5. Configure web server
6. Optionally install SSL

## Manual Installation

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_IP

# Clone repository
sudo mkdir -p /opt/aivision && sudo chown ubuntu:ubuntu /opt/aivision
cd /opt/aivision && git clone https://github.com/akhanna222/AIVision.git .

# Configure
cp .env.example .env
nano .env  # Add API keys

# Deploy
sudo chmod +x deploy/scripts/deploy.sh
sudo ./deploy/scripts/deploy.sh
```

## Access URLs

After installation:
- Template Builder: `http://YOUR_IP/template-builder`
- Simple Extraction: `http://YOUR_IP/simple-extract`
- API Docs: `http://YOUR_IP/docs`

## Service Management

```bash
sudo systemctl status aivision    # Check status
sudo systemctl restart aivision   # Restart
sudo journalctl -u aivision -f    # View logs
```
