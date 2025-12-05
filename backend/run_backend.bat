@echo off
REM Qari App Backend Startup Script

echo ============================================
echo Starting Qari App Backend API
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if Quran database exists
if not exist "data\quran_uthmani.json" (
    echo.
    echo [2/3] Downloading Quran database...
    python scripts\download_quran_database.py
    if errorlevel 1 (
        echo ERROR: Failed to download Quran database
        pause
        exit /b 1
    )
) else (
    echo [2/3] Quran database found ^| OK
)

REM Set FFmpeg in PATH
set PATH=%CD%\bin;%PATH%

REM Start API server
echo.
echo [3/3] Starting API server...
echo.
echo ============================================
echo API will be available at:
echo   http://localhost:8000
echo   http://localhost:8000/docs (Swagger UI)
echo ============================================
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
