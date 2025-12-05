@echo off
REM ============================================================================
REM AIVision Local Setup - Simple Batch Version
REM ============================================================================
REM
REM This is a simplified setup script. For full-featured setup, use:
REM   setup-local.ps1
REM
REM ============================================================================

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║         AIVision - Local Development Setup (Windows)         ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found. Please install Python 3.11 from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Node.js not found. Please install from https://nodejs.org/
    pause
    exit /b 1
)

echo ✓ Prerequisites check passed
echo.

REM Create virtual environment
echo ▶ Creating Python virtual environment...
if exist venv (
    echo   Virtual environment already exists
) else (
    python -m venv venv
    echo ✓ Virtual environment created
)

REM Activate virtual environment and install dependencies
echo.
echo ▶ Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
echo ✓ Python dependencies installed

REM Setup frontend
echo.
echo ▶ Setting up frontend...
cd frontend
call npm install
echo ✓ Frontend dependencies installed
cd ..

REM Create .env if it doesn't exist
if not exist .env (
    echo.
    echo ▶ Creating .env file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql://aivision:password@localhost:5432/aivision
        echo.
        echo # API Keys ^(UPDATE THESE^)
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo ANTHROPIC_API_KEY=your_anthropic_api_key_here
        echo.
        echo # Application
        echo ENVIRONMENT=development
        echo DEBUG=True
        echo.
        echo # Storage ^(JSON only - no files^)
        echo STORAGE_TYPE=none
        echo STORE_ORIGINAL_FILES=false
        echo STORE_EXTRACTED_IMAGES=false
    ) > .env
    echo ✓ .env file created
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║              Setup Complete!                                  ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo Next Steps:
echo.
echo 1. Update .env with your API keys
echo 2. Setup PostgreSQL database:
echo    - Install from https://www.postgresql.org/download/windows/
echo    - Create database: aivision
echo    - Create user: aivision
echo.
echo 3. Initialize database:
echo    python -c "from app.db.session import init_db; init_db()"
echo.
echo 4. Start development:
echo    .\start-dev.ps1  (or use Docker)
echo.
pause
