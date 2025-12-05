# AIVision - Local Development Guide

Complete guide for running AIVision on your local machine (Windows, Mac, or Linux).

## 🚀 Quick Start Options

### Option 1: Docker (Recommended - Easiest)

```bash
# 1. Clone the repository
git clone <repository-url>
cd AIVision

# 2. Copy environment file and add your API keys
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Mac/Linux

# 3. Start all services
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
# pgAdmin:  http://localhost:5050
```

### Option 2: Windows PowerShell Script

```powershell
# Run the automated setup script
.\setup-local.ps1

# After setup completes:
.\start-dev.ps1
```

### Option 3: Manual Setup

See detailed instructions below for your operating system.

---

## 📋 Prerequisites

### Required Software

- **Python 3.11** or higher
- **Node.js 18** or higher
- **PostgreSQL 14** or higher
- **Git**

### API Keys (Required)

You need API keys from these providers:

1. **Google Gemini**: https://ai.google.dev/
2. **OpenAI**: https://platform.openai.com/
3. **Anthropic Claude**: https://console.anthropic.com/

---

## 🪟 Windows Setup

### Automatic Setup (Recommended)

```powershell
# Run PowerShell as Administrator
.\setup-local.ps1
```

This script will:
- ✅ Check and install prerequisites
- ✅ Setup PostgreSQL database
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Initialize database
- ✅ Setup React frontend
- ✅ Create start scripts

### Manual Windows Setup

#### 1. Install Prerequisites

```powershell
# Install Chocolatey (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required software
choco install python311 nodejs postgresql14 -y
```

#### 2. Setup Database

```powershell
# Create database and user
psql -U postgres
```

```sql
CREATE USER aivision WITH PASSWORD 'your_password';
CREATE DATABASE aivision OWNER aivision;
GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;
\q
```

#### 3. Setup Backend

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env file
copy .env.example .env

# Edit .env and add your API keys

# Initialize database
python -c "from app.db.session import init_db; init_db()"
```

#### 4. Setup Frontend

```powershell
cd frontend
npm install
cd ..
```

#### 5. Start Development

```powershell
# Start backend (in one terminal)
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev
```

---

## 🐧 Linux/Mac Setup

### Automatic Setup

```bash
# Make script executable
chmod +x setup-local.sh

# Run setup
./setup-local.sh
```

### Manual Linux/Mac Setup

#### 1. Install Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql nodejs npm
```

**Mac (with Homebrew):**
```bash
brew install python@3.11 postgresql node
```

#### 2. Setup Database

```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # Mac

# Create database
sudo -u postgres psql
```

```sql
CREATE USER aivision WITH PASSWORD 'your_password';
CREATE DATABASE aivision OWNER aivision;
GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;
\q
```

#### 3. Setup Backend

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or vim, code, etc.

# Initialize database
python -c "from app.db.session import init_db; init_db()"
```

#### 4. Setup Frontend

```bash
cd frontend
npm install
cd ..
```

#### 5. Start Development

```bash
# Start backend (in one terminal)
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd frontend
npm run dev
```

---

## 🐳 Docker Development

### Full Stack with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Individual Services

```bash
# Backend only
docker-compose up -d postgres redis backend

# Frontend only
docker-compose up -d frontend

# Database only
docker-compose up -d postgres pgadmin
```

### Useful Docker Commands

```bash
# Access backend shell
docker-compose exec backend bash

# Run tests
docker-compose exec backend pytest tests/ -v

# Access database
docker-compose exec postgres psql -U aivision -d aivision

# View backend logs
docker-compose logs -f backend

# Clean everything
docker-compose down -v
```

---

## 🧪 Running Tests

### Backend Tests

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_create_account -v

# Run tests in Docker
docker-compose exec backend pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

---

## 🔍 Accessing Services

### Development URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | - |
| Backend API | http://localhost:8000 | Bearer token |
| API Documentation | http://localhost:8000/docs | - |
| ReDoc | http://localhost:8000/redoc | - |
| pgAdmin | http://localhost:5050 | admin@aivision.local / admin |
| Database | localhost:5432 | aivision / password |

### Test Account

After setup, a test account is created:

- **Email**: test@local.dev
- **API Token**: (shown in setup output)

Use this token in API requests:
```bash
curl -H "Authorization: Bearer aiv_..." http://localhost:8000/api/v1/templates/
```

---

## 🛠️ VS Code Setup

### Recommended Extensions

Open VS Code and install recommended extensions:

```bash
code .
# Click "Install" when prompted for recommended extensions
```

Or install manually:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Docker
- PostgreSQL
- GitLens

### Debugging

Use the built-in debug configurations:

1. Press `F5` or click Run & Debug
2. Select "Python: FastAPI" to debug backend
3. Set breakpoints in your code
4. Use Debug Console for live evaluation

---

## 📝 Environment Variables

### Required Variables (.env)

```bash
# Vision Model API Keys (REQUIRED)
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database
DATABASE_URL=postgresql://aivision:password@localhost:5432/aivision

# Storage (JSON only - NO file storage)
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false
STORE_EXTRACTED_IMAGES=false
```

### Optional Variables

```bash
# Application
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Models
DEFAULT_VISION_MODEL=gemini-2.0-flash-exp
CONFIDENCE_THRESHOLD=0.70

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## 🔧 Troubleshooting

### Common Issues

#### PostgreSQL Connection Error

```
Error: could not connect to server
```

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # Mac
Get-Service postgresql*  # Windows PowerShell

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql  # Mac
```

#### Python Module Not Found

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Port Already in Use

```
Error: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

#### Node Modules Issues

```
Error: Cannot find module
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Database Migration Errors

```
Error: relation "accounts" does not exist
```

**Solution:**
```bash
# Reinitialize database
python -c "from app.db.session import init_db; init_db()"

# Or with Docker
docker-compose down -v
docker-compose up -d
```

---

## 📚 Additional Resources

### Documentation

- [API Documentation](http://localhost:8000/docs)
- [Main README](README.md)
- [Deployment Guide](deploy/README.md)

### Useful Commands

```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
pylint app/

# Database backup
pg_dump -U aivision aivision > backup.sql

# Database restore
psql -U aivision aivision < backup.sql
```

---

## 🎯 Development Workflow

### Typical Development Session

```bash
# 1. Update code
git pull origin main

# 2. Update dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Start services
docker-compose up -d
# OR
.\start-dev.ps1  # Windows
./start-dev.sh   # Linux/Mac

# 4. Make changes

# 5. Run tests
pytest tests/ -v

# 6. Commit changes
git add .
git commit -m "Your changes"
git push
```

### Hot Reload

Both backend and frontend support hot reload:

- **Backend**: Changes to `.py` files auto-reload with `--reload` flag
- **Frontend**: Changes to `.tsx`/`.ts` files trigger HMR (Hot Module Replacement)

---

## 🆘 Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Check GitHub Issues
4. Contact the team

---

## 🎉 You're Ready!

Visit http://localhost:5173 to start developing!

**Happy coding! 🚀**
