@echo off
REM Python 3.7 Wheel Installation Batch Script
REM This script helps install the downloaded wheels for Python 3.7 compatibility.

echo Python 3.7 Wheel Installation Script
echo =====================================

REM Check if Python 3.7 is available
python --version 2>nul | findstr "3.7" >nul
if %errorlevel% neq 0 (
    echo ERROR: Python 3.7 not found or not in PATH
    echo Please ensure Python 3.7 is installed and in your PATH
    pause
    exit /b 1
)

echo Python 3.7 found
echo.

REM Check if wheels directory exists
if not exist "wheels" (
    echo ERROR: Wheels directory not found
    echo Please run the wheel download first
    pause
    exit /b 1
)

echo Wheels directory found
echo.

REM Install core packages
echo Installing core packages...
pip install --find-links ./wheels --no-index pyserial==3.5 numpy==1.21.6 PyVISA==1.12.0 psutil==7.1.0 typing-extensions==4.7.1

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Core packages installed successfully!
    echo.
    echo To install additional packages, run:
    echo pip install --find-links ./wheels --no-index -r requirements_python37.txt
) else (
    echo.
    echo ERROR: Installation failed
)

echo.
pause
