# 🚀 AIVision Quick Start - Interactive Installation

The easiest way to install AIVision on your EC2 server!

---

## ⚡ One-Command Installation

```bash
# Download and run the interactive installer
curl -o install.sh https://raw.githubusercontent.com/akhanna222/AIVision/claude/ocr-service-templates-01MnNQz5UdYNuAmnsHtobQtM/install.sh
chmod +x install.sh
sudo ./install.sh
```

That's it! The installer will guide you through everything.

---

## 📋 What the Installer Does

The interactive script will:

1. ✅ **Check your system** - Detects Python, Node.js, available memory
2. ✅ **Detect port conflicts** - Finds which ports are already in use
3. ✅ **Ask configuration questions** - Domain, API keys, deployment mode
4. ✅ **Install all dependencies** - PostgreSQL, Nginx, Python packages, Node.js
5. ✅ **Setup database** - Creates database and user automatically
6. ✅ **Build frontend** - Compiles React app for production
7. ✅ **Configure services** - Sets up systemd and Nginx
8. ✅ **Start everything** - Launches all services
9. ✅ **Install SSL** (optional) - Free Let's Encrypt certificate

**Estimated time:** 10-15 minutes

---

## 🎯 What You'll Be Asked

### 1. Deployment Mode

The installer detects your port usage and offers options:

**If ports 80/443 are FREE:**
- Standard deployment on ports 80/443
- Subdomain deployment (e.g., ocr.epingu.org)

**If ports 80/443 are IN USE:**
- Path-based routing (`/ocr/*` on your existing Nginx)
- Different ports (8080/8443)
- Subdomain with custom ports

### 2. API Keys

You need at least ONE:
- **Gemini** (FREE, recommended) - Get from: https://makersuite.google.com/app/apikey
- **OpenAI** (Paid, optional) - Get from: https://platform.openai.com/api-keys
- **Anthropic** (Paid, optional) - Get from: https://console.anthropic.com/

### 3. Domain (Optional)

If you have a domain like `epingu.org`, you can:
- Use subdomain: `ocr.epingu.org`
- Get free SSL certificate automatically
- Professional URLs for your users

### 4. Database

The installer will ask for:
- Database name (default: `aivision`)
- Database user (default: `aivision`)
- Password (auto-generated or custom)

---

## 📺 Example Installation

Here's what the installation looks like:

```bash
$ sudo ./install.sh

╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║              🚀 AIVision OCR Interactive Installer 🚀                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

[INFO] This installer will:
  1. Check your system requirements
  2. Detect port conflicts
  3. Configure deployment options
  4. Install all dependencies
  5. Setup database and services
  6. Configure web server

Press Enter to continue...

==> Step 1: Checking System Requirements

[INFO] OS: Ubuntu 22.04.3 LTS
✓ Found: python3.10 (version 3.10.12)
✓ Found: Node.js v18.17.0
[INFO] Available RAM: 4096MB

==> Step 2: Detecting Port Usage

[WARN] Port 80 is in use
[WARN] Port 443 is in use
[WARN] Port 8000 is in use
✓ Port 3000 is available

==> Step 3: Deployment Configuration

[WARN] Ports 80/443 are in use. You have these options:

  1) Path-based routing    - Add /ocr/* routes to existing Nginx
                             URLs: http://your-ip/ocr/template-builder

  2) Different ports       - Run on ports 8080/8443
                             URLs: http://your-ip:8080/template-builder

  3) Subdomain             - Use ocr.epingu.org (requires DNS)
                             URLs: https://ocr.epingu.org/template-builder

Enter your choice (1-3) [default: 1]: 1

==> Step 4: API Keys Configuration

[INFO] You need at least ONE API key. Gemini is FREE!

Get API keys from:
  • Gemini (FREE):     https://makersuite.google.com/app/apikey
  • OpenAI (Paid):     https://platform.openai.com/api-keys
  • Anthropic (Paid):  https://console.anthropic.com/

Enter Gemini API key: AIzaSy...
Enter OpenAI API key (optional):
Enter Anthropic API key (optional):

==> Configuration Summary

Deployment Configuration:
  Installation Directory: /opt/aivision
  Python Command: python3.10
  Backend Port: 8001
  Deployment Mode: Path-based routing (/ocr/*)

Database Configuration:
  Database: aivision
  User: aivision
  Password: wX7k... (saved to /opt/aivision/.db_credentials)

API Keys:
  ✓ Gemini API configured

Proceed with installation? (y/n): y

==> Starting Installation

[INFO] Updating system packages...
[INFO] Installing system packages...
✓ Dependencies installed

==> Downloading AIVision

[INFO] Cloning repository...
✓ Code downloaded

==> Setting up PostgreSQL Database

[INFO] Creating database and user...
✓ Database created: aivision

... (continues with all installation steps)

╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           ✅ Installation Complete! ✅                                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

Access Your AIVision Installation:

  Template Builder:  http://your-ip/ocr/template-builder
  Simple Extraction: http://your-ip/ocr/simple-extract
  API Docs:          http://your-ip/ocr/docs

Service Management:
  Check status:   sudo systemctl status aivision
  View logs:      sudo journalctl -u aivision -f
  Restart:        sudo systemctl restart aivision
```

---

## 🌐 After Installation

### Access Your UIs

Depending on your deployment mode, access AIVision at:

**Path-based routing:**
```
http://YOUR_IP/ocr/template-builder
http://YOUR_IP/ocr/simple-extract
```

**Different ports:**
```
http://YOUR_IP:8080/template-builder
http://YOUR_IP:8080/simple-extract
```

**Subdomain:**
```
https://ocr.epingu.org/template-builder
https://ocr.epingu.org/simple-extract
```

### Test the Installation

1. **Open Template Builder** in your browser
2. **Create a template:**
   - Click "Mortgage Documents" for preset
   - Or add custom fields
   - Click "Save Template"
   - Copy the API endpoint

3. **Test Extraction:**
   - Go to Simple Extraction UI
   - Select your template
   - Upload a document (PDF, JPG, PNG)
   - Click "Extract Document"
   - View the results!

---

## 🔧 Post-Installation Management

### Service Commands

```bash
# Check service status
sudo systemctl status aivision

# View real-time logs
sudo journalctl -u aivision -f

# Restart service
sudo systemctl restart aivision

# Stop service
sudo systemctl stop aivision

# Start service
sudo systemctl start aivision
```

### Configuration Files

```bash
# Main environment configuration
sudo nano /opt/aivision/.env

# Nginx configuration
sudo nano /etc/nginx/sites-available/aivision

# After changes, restart services
sudo systemctl restart aivision
sudo systemctl reload nginx
```

### Database Access

```bash
# View database credentials
cat /opt/aivision/.db_credentials

# Connect to database
sudo -u postgres psql aivision

# Backup database
sudo -u postgres pg_dump aivision > backup.sql
```

### Logs

```bash
# Backend logs (real-time)
sudo journalctl -u aivision -f

# Application logs
sudo tail -f /var/log/aivision/access.log
sudo tail -f /var/log/aivision/error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 🔄 Updating AIVision

To update to the latest version:

```bash
cd /opt/aivision

# Pull latest code
sudo -u ubuntu git pull origin claude/ocr-service-templates-01MnNQz5UdYNuAmnsHtobQtM

# Update dependencies
sudo -u ubuntu venv/bin/pip install -r requirements.txt

# Rebuild frontend
cd frontend
sudo -u ubuntu npm install
sudo -u ubuntu npm run build
cd ..

# Restart services
sudo systemctl restart aivision
sudo systemctl reload nginx
```

---

## 🆘 Troubleshooting

### Installation Failed

If installation fails:

```bash
# Check the error message and logs
sudo journalctl -u aivision -n 50

# Common fixes:
# 1. Ensure all ports are available
# 2. Check API keys are valid
# 3. Verify Python 3.8+ is installed
# 4. Ensure PostgreSQL is running

# Re-run installer
sudo ./install.sh
```

### Service Won't Start

```bash
# Check service status
sudo systemctl status aivision

# View detailed error
sudo journalctl -u aivision -n 100 --no-pager

# Common issues:
# - Port already in use: Change BACKEND_PORT in .env
# - Database connection: Check .db_credentials
# - Python errors: Verify venv and dependencies
```

### Can't Access UI

```bash
# Check Nginx is running
sudo systemctl status nginx

# Test backend directly
curl http://localhost:8001/health

# Test through Nginx
curl http://localhost/ocr/health  # Path-based
curl http://localhost:8080/health  # Different ports

# Check firewall
sudo ufw status

# Verify security group (AWS EC2)
# Ensure ports 80, 443 (or 8080, 8443) are open
```

### SSL Certificate Issues

```bash
# Re-install certificate
sudo certbot --nginx -d ocr.epingu.org --force-renewal

# Check certificate status
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run
```

---

## 📚 Additional Documentation

For detailed configuration and advanced topics, see:

- **DEPLOY_CUSTOM_PORTS.md** - Running alongside other apps
- **DEPLOY_EPINGU_ORG.md** - Domain-specific deployment
- **README_PUBLIC_UI_ACCESS.md** - Public access configuration
- **README_AWS_EC2.md** - AWS EC2 deployment guide

---

## 💡 Tips

1. **Use Gemini API** - It's free and works great for most documents
2. **Enable multi-model** - For higher accuracy, use hybrid strategy
3. **Monitor logs** - Keep an eye on `/var/log/aivision/` for issues
4. **Backup database** - Regular backups prevent data loss
5. **Update regularly** - Pull latest code for new features and fixes

---

## 🎉 Success!

You now have a fully functional OCR service running!

**What you can do:**
- ✅ Create unlimited custom templates
- ✅ Extract data from PDFs, images, and documents
- ✅ Use multiple AI models (Gemini, GPT-4, Claude)
- ✅ Access via web UI or API
- ✅ No authentication required for public templates
- ✅ Scale to handle thousands of documents

**Share these URLs** with your team:
- Template Builder (create templates)
- Simple Extraction (extract data)
- API Docs (for developers)

Enjoy your AIVision OCR service! 🚀
