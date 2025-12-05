# 💻 Quick Start: Running Locally on Windows

Complete guide to run AIVision OCR service on your Windows machine with VS Code or Cursor IDE.

---

## 📋 Prerequisites

- **Windows 10/11**
- **VS Code** or **Cursor (Antigravity) IDE**
- **Git** (download from [git-scm.com](https://git-scm.com/))
- **At least ONE API key** (Gemini is FREE!)

---

## 🔑 Step 1: Get Your API Keys (5 minutes)

You need **at least ONE** API key. **Gemini is FREE** and perfect for development!

### Option A: Google Gemini (FREE) ⭐ Recommended

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. **Cost**: FREE (60 requests/minute)

### Option B: OpenAI GPT-4o (Paid)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create account + add payment method
3. Create API key (starts with `sk-...`)
4. **Cost**: ~$0.30 per 1000 documents (GPT-4o-mini)

### Option C: Anthropic Claude (Paid)

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create account + add payment method
3. Create API key (starts with `sk-ant-...`)
4. **Cost**: ~$0.50 per 1000 documents (Haiku 4)

💡 **For Development**: Just Gemini (free) is enough!

---

## 🚀 Method 1: Automated Setup (PowerShell) - Recommended

### One-Command Installation

1. **Open PowerShell as Administrator**:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Clone Repository**:
   ```powershell
   cd C:\
   git clone https://github.com/your-org/AIVision.git
   cd AIVision
   ```

3. **Run Setup Script**:
   ```powershell
   .\setup-local.ps1
   ```

4. **Enter Your API Keys** when prompted:
   ```
   Enter Gemini API Key (or press Enter to skip): AIzaSy_your_key
   Enter OpenAI API Key (or press Enter to skip): [Enter]
   Enter Anthropic API Key (or press Enter to skip): [Enter]
   ```

### What the Script Does:

✅ Checks for Python, Node.js, PostgreSQL
✅ Auto-installs missing software via Chocolatey
✅ Creates PostgreSQL database
✅ Sets up Python virtual environment
✅ Installs all dependencies
✅ Runs database migrations
✅ Creates test account
✅ Displays API token for testing

**Wait 10-15 minutes** for completion.

### Start Services

```powershell
# Terminal 1: Start Backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend
npm run dev
```

**Access**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🐳 Method 2: Docker (Easiest)

### Prerequisites

- **Docker Desktop** ([download](https://www.docker.com/products/docker-desktop/))

### Setup

1. **Install Docker Desktop** and start it

2. **Clone Repository**:
   ```powershell
   cd C:\
   git clone https://github.com/your-org/AIVision.git
   cd AIVision
   ```

3. **Create `.env` file**:
   ```powershell
   notepad .env
   ```

   Paste this:
   ```bash
   # Database
   DATABASE_URL=postgresql://aivision:aivision_dev_password@postgres:5432/aivision

   # API Keys (add at least one)
   GEMINI_API_KEY=AIzaSy_your_actual_key
   OPENAI_API_KEY=
   ANTHROPIC_API_KEY=

   # Development Settings
   DEBUG=true
   STORAGE_TYPE=none
   STORE_ORIGINAL_FILES=false
   ```

4. **Start Everything**:
   ```powershell
   docker-compose up -d
   ```

5. **Check Logs**:
   ```powershell
   docker-compose logs -f
   ```

**Access**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (admin@admin.com / admin)

### Docker Commands

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

---

## 🛠️ Method 3: Manual Setup (Full Control)

### Step 1: Install Prerequisites (15 minutes)

#### Install Chocolatey (Package Manager)

Open PowerShell as Administrator:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### Install Software

```powershell
# Install Python 3.11
choco install python311 -y

# Install Node.js 18
choco install nodejs --version=18.0.0 -y

# Install PostgreSQL 14
choco install postgresql14 --params '/Password:postgres' -y

# Refresh environment
refreshenv
```

### Step 2: Setup PostgreSQL (5 minutes)

```powershell
# Start PostgreSQL service
Start-Service postgresql-x64-14

# Create database
psql -U postgres -c "CREATE DATABASE aivision;"
psql -U postgres -c "CREATE USER aivision WITH PASSWORD 'aivision_dev';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE aivision TO aivision;"
```

### Step 3: Setup Backend (10 minutes)

```powershell
# Clone repository
cd C:\
git clone https://github.com/your-org/AIVision.git
cd AIVision

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env file
notepad .env
```

Paste this configuration:

```bash
# Database
DATABASE_URL=postgresql://aivision:aivision_dev@localhost:5432/aivision

# API Keys (add at least one)
GEMINI_API_KEY=AIzaSy_your_actual_key_here
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Application
SECRET_KEY=dev-secret-key-change-in-production
APP_ENV=development
DEBUG=true

# Storage (JSON only - no file storage)
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Multi-Model Settings
DEFAULT_EXTRACTION_STRATEGY=sequential
CONFIDENCE_THRESHOLD=0.80
FIELD_CONFIDENCE_THRESHOLD=0.70
MAX_MODELS_TO_TRY=3
```

### Step 4: Run Database Migrations

```powershell
# Initialize database
python -c "from app.db.session import init_db; init_db()"

# Run migrations
python migrations/run_migration.py
```

### Step 5: Setup Frontend (5 minutes)

```powershell
# Open new terminal
cd C:\AIVision\frontend

# Install dependencies
npm install

# Create .env file
notepad .env.local
```

Paste this:

```
VITE_API_URL=http://localhost:8000
```

### Step 6: Start Services

**Terminal 1 (Backend)**:
```powershell
cd C:\AIVision
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend)**:
```powershell
cd C:\AIVision\frontend
npm run dev
```

---

## 🎨 Setting Up VS Code / Cursor IDE

### Install Extensions

1. **Open VS Code/Cursor**
2. **Install Recommended Extensions** (press `Ctrl+Shift+P` → "Extensions: Show Recommended Extensions"):
   - Python
   - Pylance
   - Python Debugger
   - SQLTools
   - SQLTools PostgreSQL Driver
   - ESLint
   - Prettier
   - Tailwind CSS IntelliSense
   - Thunder Client (API testing)

### VS Code Configuration

The repository includes `.vscode/` folder with:
- ✅ `settings.json` - Python interpreter, formatting
- ✅ `extensions.json` - Recommended extensions
- ✅ `launch.json` - Debug configurations

### Debug Backend

1. Press `F5` or click "Run and Debug"
2. Select "**Python: FastAPI**"
3. Set breakpoints in your code
4. API runs on http://localhost:8000

### Debug Frontend

1. Start frontend: `npm run dev`
2. Press `F5`
3. Select "**Chrome**" or "**Edge**"

### Run Tests in VS Code

1. Open Testing sidebar (`Ctrl+Shift+T`)
2. Click "Configure Python Tests"
3. Select "pytest"
4. Tests will appear in sidebar
5. Click play button to run

---

## ✅ Verify Installation

### Check Services

```powershell
# Check PostgreSQL
Get-Service postgresql-x64-14

# Check if backend is running
curl http://localhost:8000/health

# Check if frontend is running
curl http://localhost:5173
```

### Open Web Interface

**Browser**: http://localhost:5173

---

## 🎯 Create Test Account & Test API

### Create Account

```powershell
# Using PowerShell
$body = @{
    name = "Test Account"
    email = "test@example.com"
    plan = "professional"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/accounts" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Save the API token** from response!

### Test with Thunder Client (VS Code)

1. **Install Thunder Client** extension
2. **Create New Request**
3. **POST** `http://localhost:8000/api/v1/extractions/extract-multi-model`
4. **Headers**:
   - `Authorization: Bearer YOUR_API_TOKEN`
5. **Body** (Form):
   - `file`: Select invoice.pdf
   - `models`: `gemini-2.0-flash-exp,gpt-4o`
   - `strategy`: `hybrid`
   - `confidence_threshold`: `0.80`
6. **Send**

### Test with curl (Git Bash)

```bash
curl -X POST http://localhost:8000/api/v1/extractions/extract-multi-model \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@invoice.pdf" \
  -F "models=gemini-2.0-flash-exp" \
  -F "strategy=sequential"
```

---

## 🧪 Run Tests

### Backend Tests

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_multi_model.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

```powershell
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

---

## 🔧 Troubleshooting

### Port Already in Use

```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### PostgreSQL Won't Start

```powershell
# Check service status
Get-Service postgresql-x64-14

# Start service
Start-Service postgresql-x64-14

# If fails, restart computer
```

### Python Not Found

```powershell
# Check Python installation
python --version

# If not found, reinstall
choco install python311 -y
refreshenv
```

### Can't Connect to Database

```powershell
# Test connection
psql -U aivision -d aivision -h localhost

# If password fails, reset:
psql -U postgres -c "ALTER USER aivision WITH PASSWORD 'aivision_dev';"
```

### Virtual Environment Issues

```powershell
# Delete and recreate
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Won't Start

```powershell
# Delete node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
npm run dev
```

---

## 🎯 Multi-Model Extraction Examples

### Example 1: Single Free Model (Development)

```powershell
curl -X POST http://localhost:8000/api/v1/extractions/extract-multi-model `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -F "file=@invoice.pdf" `
  -F "models=gemini-2.0-flash-exp" `
  -F "strategy=sequential"
```

### Example 2: Hybrid Strategy (Recommended)

```powershell
curl -X POST http://localhost:8000/api/v1/extractions/extract-multi-model `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -F "file=@invoice.pdf" `
  -F "models=gemini-2.0-flash-exp,gpt-4o-mini" `
  -F "strategy=hybrid" `
  -F "confidence_threshold=0.85"
```

### Example 3: Maximum Accuracy (Parallel)

```powershell
curl -X POST http://localhost:8000/api/v1/extractions/extract-multi-model `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -F "file=@document.pdf" `
  -F "models=gemini-2.0-flash-exp,gpt-4o,claude-sonnet-4-20250514" `
  -F "strategy=parallel"
```

---

## 📚 API Documentation

Access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🔄 Development Workflow

### Daily Development

```powershell
# Start backend
cd C:\AIVision
.\venv\Scripts\activate
uvicorn app.main:app --reload

# In another terminal: Start frontend
cd C:\AIVision\frontend
npm run dev
```

### Make Code Changes

1. **Backend changes**: Auto-reloads with `--reload` flag
2. **Frontend changes**: Auto-reloads with Vite HMR
3. **Database changes**: Run migrations

### Run Tests Before Commit

```powershell
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Linting
flake8 app/
cd frontend && npm run lint
```

### Commit Changes

```powershell
git add .
git commit -m "feat: your feature description"
git push
```

---

## 🐛 Debugging Tips

### Debug Backend in VS Code

1. Set breakpoint in code (click left of line number)
2. Press `F5` → Select "Python: FastAPI"
3. Send API request
4. Debugger stops at breakpoint
5. Inspect variables, step through code

### Debug Frontend in Browser

1. Start frontend: `npm run dev`
2. Open http://localhost:5173
3. Press `F12` (DevTools)
4. Go to "Sources" tab
5. Set breakpoints in TypeScript files
6. Interact with UI

### View Database

**Option 1: pgAdmin** (if using Docker)
- URL: http://localhost:5050
- Email: admin@admin.com
- Password: admin

**Option 2: SQLTools in VS Code**
1. Install SQLTools extension
2. Click "Add Connection"
3. Select PostgreSQL
4. Enter:
   - Host: localhost
   - Port: 5432
   - Database: aivision
   - Username: aivision
   - Password: aivision_dev
5. Connect and browse tables

**Option 3: psql Command Line**
```powershell
psql -U aivision -d aivision -h localhost
```

---

## 📁 Project Structure

```
AIVision/
├── app/                          # Backend
│   ├── api/v1/                  # API endpoints
│   │   └── extractions.py       # Extraction endpoints
│   ├── core/                    # Core functionality
│   ├── db/                      # Database
│   │   ├── models.py           # SQLAlchemy models
│   │   └── crud.py             # Database operations
│   ├── services/                # Business logic
│   │   └── multi_model_extractor.py  # Multi-model extraction
│   └── main.py                 # FastAPI app
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   └── App.tsx             # Main app
│   └── package.json
├── tests/                       # Backend tests
│   ├── test_api.py
│   └── test_multi_model.py
├── migrations/                  # Database migrations
├── .env                        # Environment config
├── .vscode/                    # VS Code settings
├── docker-compose.yml          # Docker setup
├── requirements.txt            # Python dependencies
└── README.md                   # Main documentation
```

---

## 🆘 Need Help?

- **Full AWS Deployment**: See `README_AWS_EC2.md`
- **Detailed Local Setup**: See `LOCAL_DEVELOPMENT.md`
- **API Documentation**: http://localhost:8000/docs
- **Logs**: Check terminal output
- **Database Issues**: See troubleshooting section above

---

## 🎓 Learning Resources

### Backend (Python/FastAPI)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Python Async/Await](https://realpython.com/async-io-python/)

### Frontend (React/TypeScript)
- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)

### AI Vision APIs
- [Google Gemini API](https://ai.google.dev/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com/)

---

## 📝 Quick Reference

```powershell
# Start backend
.\venv\Scripts\activate
uvicorn app.main:app --reload

# Start frontend
cd frontend && npm run dev

# Run tests
pytest tests/ -v

# Run migrations
python migrations/run_migration.py

# Check database
psql -U aivision -d aivision

# Docker commands
docker-compose up -d
docker-compose logs -f
docker-compose down

# Port check
netstat -ano | findstr :8000
```

---

**🎉 Congratulations!** AIVision OCR is running locally on your Windows machine!

**Access Points**:
- 🌐 Frontend: http://localhost:5173 (or 3000 with Docker)
- 🔌 API: http://localhost:8000
- 📚 Docs: http://localhost:8000/docs
- 🗃️ pgAdmin: http://localhost:5050 (Docker only)

**Estimated Setup Time**: 20-30 minutes
**Cost**: $0 (using free Gemini API)
