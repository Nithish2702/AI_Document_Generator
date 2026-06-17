@echo off
echo ============================================================
echo   AI Document Generator - Bulk Upload Script
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if backend is running
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ERROR: Backend server is not running!
    echo Please start the backend first:
    echo   uvicorn app.main:app --reload
    echo.
    pause
    exit /b 1
)

echo Backend server is running...
echo.

REM Prompt for documents folder
set /p DOCS_FOLDER="Enter path to your Documents folder (or press Enter for default): "

if "%DOCS_FOLDER%"=="" (
    set DOCS_FOLDER=..\..\Documents
)

echo.
echo Uploading documents from: %DOCS_FOLDER%
echo.

REM Run the Python upload script
python upload_documents.py "%DOCS_FOLDER%"

echo.
echo ============================================================
pause
