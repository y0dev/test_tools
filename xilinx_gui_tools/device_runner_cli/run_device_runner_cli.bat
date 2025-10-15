@echo off
REM Launch Device Runner CLI (Windows)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Starting Device Runner CLI...
echo.

REM Check if Tcl is available
tclsh -c "puts \"Tcl version: [info patchlevel]\"" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Tcl/Tk not found in PATH
    echo Please install Tcl/Tk or add it to your PATH
    echo.
    echo You can download Tcl/Tk from:
    echo https://www.tcl.tk/software/tcltk/
    echo.
    pause
    exit /b 1
)

echo Tcl/Tk found, launching Device Runner CLI...
echo.

REM Launch the CLI application
tclsh "%SCRIPT_DIR%device_runner_cli.tcl" %*

echo.
echo Device Runner CLI exited
pause
