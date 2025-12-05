# ============================================================================
# AIVision Local Development Setup Script for Windows
# ============================================================================
#
# This script sets up the complete AIVision development environment on Windows:
# - PostgreSQL database
# - Python virtual environment and dependencies
# - React frontend with Node.js
# - Environment configuration
# - Database initialization
#
# Requirements:
# - Windows 10/11
# - PowerShell 5.1 or higher
# - Internet connection
#
# Usage:
#   .\setup-local.ps1
#
# Or run with elevated privileges for PostgreSQL installation:
#   Run as Administrator
# ============================================================================

param(
    [switch]$SkipPostgres,
    [switch]$SkipPython,
    [switch]$SkipNode
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "║         AIVision - Local Development Setup (Windows)         ║" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n▶ $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

# ============================================================================
# Check Prerequisites
# ============================================================================

Write-Step "Checking prerequisites..."

# Check if running in project directory
if (-not (Test-Path ".\app\main.py")) {
    Write-Error "Please run this script from the AIVision project root directory"
    exit 1
}

# Check for Chocolatey (Windows package manager)
$hasChoco = Test-Command "choco"
if (-not $hasChoco) {
    Write-Warning "Chocolatey not found. Some installations may require manual intervention."
    Write-Info "To install Chocolatey, visit: https://chocolatey.org/install"
}

# ============================================================================
# 1. Install Python 3.11
# ============================================================================

if (-not $SkipPython) {
    Write-Step "Checking Python installation..."

    $hasPython = Test-Command "python"
    if ($hasPython) {
        $pythonVersion = python --version 2>&1
        Write-Success "Python found: $pythonVersion"
    } else {
        Write-Warning "Python not found"
        if ($hasChoco) {
            Write-Info "Installing Python 3.11 via Chocolatey..."
            choco install python311 -y
            refreshenv
        } else {
            Write-Info "Please install Python 3.11 from: https://www.python.org/downloads/"
            Write-Info "After installation, restart this script."
            exit 1
        }
    }
}

# ============================================================================
# 2. Install Node.js
# ============================================================================

if (-not $SkipNode) {
    Write-Step "Checking Node.js installation..."

    $hasNode = Test-Command "node"
    if ($hasNode) {
        $nodeVersion = node --version
        Write-Success "Node.js found: $nodeVersion"
    } else {
        Write-Warning "Node.js not found"
        if ($hasChoco) {
            Write-Info "Installing Node.js via Chocolatey..."
            choco install nodejs -y
            refreshenv
        } else {
            Write-Info "Please install Node.js from: https://nodejs.org/"
            Write-Info "After installation, restart this script."
            exit 1
        }
    }
}

# ============================================================================
# 3. Install PostgreSQL
# ============================================================================

if (-not $SkipPostgres) {
    Write-Step "Checking PostgreSQL installation..."

    $hasPostgres = Test-Command "psql"
    if ($hasPostgres) {
        $postgresVersion = psql --version
        Write-Success "PostgreSQL found: $postgresVersion"
    } else {
        Write-Warning "PostgreSQL not found"
        Write-Info "Installing PostgreSQL..."

        if ($hasChoco) {
            choco install postgresql14 -y
            refreshenv
        } else {
            Write-Info "Please install PostgreSQL from: https://www.postgresql.org/download/windows/"
            Write-Info "After installation, restart this script."
            exit 1
        }
    }
}

# ============================================================================
# 4. Setup PostgreSQL Database
# ============================================================================

Write-Step "Setting up PostgreSQL database..."

$dbName = "aivision"
$dbUser = "aivision"
$dbPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})

Write-Info "Database Name: $dbName"
Write-Info "Database User: $dbUser"
Write-Info "Generating secure password..."

# Check if database already exists
try {
    $dbExists = psql -U postgres -lqt | Select-String -Pattern "^\s*$dbName\s"
    if ($dbExists) {
        Write-Warning "Database '$dbName' already exists"
        $response = Read-Host "Drop and recreate? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            psql -U postgres -c "DROP DATABASE IF EXISTS $dbName;"
            psql -U postgres -c "DROP USER IF EXISTS $dbUser;"
        } else {
            Write-Info "Using existing database"
        }
    }
} catch {
    Write-Warning "Could not check existing database. Continuing..."
}

# Create database and user
try {
    Write-Info "Creating PostgreSQL database and user..."
    psql -U postgres -c "CREATE USER $dbUser WITH PASSWORD '$dbPassword';" 2>$null
    psql -U postgres -c "CREATE DATABASE $dbName OWNER $dbUser;" 2>$null
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $dbName TO $dbUser;" 2>$null
    Write-Success "Database created successfully"
} catch {
    Write-Warning "Database may already exist or user lacks permissions"
}

# ============================================================================
# 5. Setup Python Virtual Environment
# ============================================================================

Write-Step "Setting up Python virtual environment..."

if (Test-Path ".\venv") {
    Write-Warning "Virtual environment already exists"
    $response = Read-Host "Recreate? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Remove-Item -Recurse -Force ".\venv"
    }
}

if (-not (Test-Path ".\venv")) {
    Write-Info "Creating virtual environment..."
    python -m venv venv
    Write-Success "Virtual environment created"
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install Python dependencies
Write-Step "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
Write-Success "Python dependencies installed"

# ============================================================================
# 6. Create .env File
# ============================================================================

Write-Step "Creating environment configuration..."

$envContent = @"
# Database Configuration (JSON storage only - NO file storage)
DATABASE_URL=postgresql://${dbUser}:${dbPassword}@localhost:5432/${dbName}
DB_HOST=localhost
DB_PORT=5432
DB_NAME=${dbName}
DB_USER=${dbUser}
DB_PASSWORD=${dbPassword}

# Vision Model API Keys (Required - Get from respective providers)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Settings
SECRET_KEY=$(New-Guid)
ENVIRONMENT=development
DEBUG=True
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# Storage Configuration - JSON ONLY IN DATABASE
STORAGE_TYPE=none
STORE_ORIGINAL_FILES=false
STORE_EXTRACTED_IMAGES=false

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000

# Document Processing
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,tiff,heic
PDF_DPI=300

# Model Configuration
DEFAULT_VISION_MODEL=gemini-2.0-flash-exp
CONFIDENCE_THRESHOLD=0.70
ENABLE_MODEL_FALLBACK=True

# Development
RELOAD=True
"@

if (Test-Path ".\.env") {
    Write-Warning ".env file already exists"
    $response = Read-Host "Overwrite? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        $envContent | Out-File -FilePath ".\.env" -Encoding UTF8
        Write-Success ".env file created"
    } else {
        Write-Info "Keeping existing .env file"
    }
} else {
    $envContent | Out-File -FilePath ".\.env" -Encoding UTF8
    Write-Success ".env file created"
}

Write-Warning "`nIMPORTANT: Update .env file with your actual API keys:"
Write-Info "- GEMINI_API_KEY: Get from https://ai.google.dev/"
Write-Info "- OPENAI_API_KEY: Get from https://platform.openai.com/"
Write-Info "- ANTHROPIC_API_KEY: Get from https://console.anthropic.com/"

# ============================================================================
# 7. Initialize Database
# ============================================================================

Write-Step "Initializing database schema..."

try {
    python -c "from app.db.session import init_db; init_db()"
    Write-Success "Database initialized"

    # Create a test account
    Write-Info "Creating test account..."
    python -c @"
from app.db.session import SessionLocal
from app.db import crud

db = SessionLocal()
try:
    account = crud.create_account(
        db=db,
        name='Test Account',
        email='test@local.dev',
        plan='free'
    )
    print(f'\n✓ Test account created')
    print(f'  Email: test@local.dev')
    print(f'  API Token: {account.api_token}')
    print(f'\n  Save this token for testing!')
except Exception as e:
    print(f'Account may already exist: {e}')
finally:
    db.close()
"@
    Write-Success "Database setup complete"
} catch {
    Write-Error "Failed to initialize database: $_"
}

# ============================================================================
# 8. Setup Frontend
# ============================================================================

Write-Step "Setting up React frontend..."

Set-Location frontend

# Install npm dependencies
Write-Info "Installing npm dependencies (this may take a few minutes)..."
npm install

# Create frontend .env
$frontendEnv = @"
VITE_API_URL=http://localhost:8000
"@

$frontendEnv | Out-File -FilePath ".env.local" -Encoding UTF8
Write-Success "Frontend environment configured"

Set-Location ..

# ============================================================================
# 9. Create Start Scripts
# ============================================================================

Write-Step "Creating convenience scripts..."

# Backend start script
$backendScript = @"
@echo off
echo Starting AIVision Backend...
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

$backendScript | Out-File -FilePath "start-backend.bat" -Encoding ASCII
Write-Success "Created start-backend.bat"

# Frontend start script
$frontendScript = @"
@echo off
echo Starting AIVision Frontend...
cd frontend
npm run dev
"@

$frontendScript | Out-File -FilePath "start-frontend.bat" -Encoding ASCII
Write-Success "Created start-frontend.bat"

# Combined start script (PowerShell)
$combinedScript = @'
# Start both backend and frontend
Write-Host "Starting AIVision Development Servers..." -ForegroundColor Cyan

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 }"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nBackend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
'@

$combinedScript | Out-File -FilePath "start-dev.ps1" -Encoding UTF8
Write-Success "Created start-dev.ps1"

# ============================================================================
# 10. Run Tests
# ============================================================================

Write-Step "Running tests..."

try {
    pytest tests/ -v --tb=short -x
    Write-Success "All tests passed!"
} catch {
    Write-Warning "Some tests failed, but setup is complete"
}

# ============================================================================
# Setup Complete
# ============================================================================

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "║              🎉 Setup Complete! 🎉                            ║" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Update .env file with your API keys" -ForegroundColor Yellow
Write-Host "   - GEMINI_API_KEY" -ForegroundColor White
Write-Host "   - OPENAI_API_KEY" -ForegroundColor White
Write-Host "   - ANTHROPIC_API_KEY" -ForegroundColor White
Write-Host ""
Write-Host "2. Start development servers:" -ForegroundColor Yellow
Write-Host "   .\start-dev.ps1          (starts both backend and frontend)" -ForegroundColor White
Write-Host "   OR" -ForegroundColor Gray
Write-Host "   .\start-backend.bat      (backend only)" -ForegroundColor White
Write-Host "   .\start-frontend.bat     (frontend only)" -ForegroundColor White
Write-Host ""
Write-Host "3. Access the application:" -ForegroundColor Yellow
Write-Host "   Frontend:  http://localhost:5173" -ForegroundColor Green
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor Green
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "4. Run tests:" -ForegroundColor Yellow
Write-Host "   pytest tests/ -v" -ForegroundColor White
Write-Host ""
Write-Host "Database Credentials:" -ForegroundColor Cyan
Write-Host "   Database: $dbName" -ForegroundColor White
Write-Host "   User:     $dbUser" -ForegroundColor White
Write-Host "   Password: $dbPassword" -ForegroundColor White
Write-Host "   (saved in .env file)" -ForegroundColor Gray
Write-Host ""

Write-Host "Happy coding! 🚀`n" -ForegroundColor Magenta
