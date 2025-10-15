@echo off
REM Launch Device Runner (Windows)
REM This script launches the Device Runner Tcl/Tk application
REM
REM Usage:
REM   run_device_runner.bat [options]
REM
REM Options:
REM   --xsdb-path <path>     Path to XSDB executable
REM   --jtag-tcp <host:port> JTAG TCP configuration (e.g., 192.168.1.100:3121)
REM   --help                Show this help message

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo.
echo ========================================
echo    Device Runner v1.0.0 - Windows
echo ========================================
echo.

REM Parse command line arguments
set XSDB_PATH=
set JTAG_TCP=
set HELP_SHOWN=0

:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="--xsdb-path" (
    set XSDB_PATH=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--jtag-tcp" (
    set JTAG_TCP=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Usage: run_device_runner.bat [options]
    echo.
    echo Options:
    echo   --xsdb-path ^<path^>     Path to XSDB executable
    echo   --jtag-tcp ^<host:port^> JTAG TCP configuration
    echo   --help                Show this help message
    echo.
    echo Examples:
    echo   run_device_runner.bat
    echo   run_device_runner.bat --xsdb-path "C:\Xilinx\Vitis\2023.2\bin\xsdb.bat"
    echo   run_device_runner.bat --jtag-tcp "192.168.1.100:3121"
    echo   run_device_runner.bat --xsdb-path "C:\Xilinx\Vitis\2023.2\bin\xsdb.bat" --jtag-tcp "192.168.1.100:3121"
    echo.
    set HELP_SHOWN=1
    goto :args_done
)
shift
goto :parse_args

:args_done

REM Check if Tcl is available
tclsh -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Tcl/Tk is not installed or not in PATH
    echo Please install ActiveTcl or Tcl/Tk and try again
    echo Download from: https://www.activestate.com/products/tcl/
    echo.
    pause
    exit /b 1
)

REM Display configuration
if not "%XSDB_PATH%"=="" (
    echo XSDB Path: %XSDB_PATH%
)
if not "%JTAG_TCP%"=="" (
    echo JTAG TCP: %JTAG_TCP%
)

if %HELP_SHOWN%==1 (
    pause
    exit /b 0
)

echo Launching Device Runner UI...
echo.

REM Launch the application with any passed arguments
if not "%XSDB_PATH%"=="" (
    if not "%JTAG_TCP%"=="" (
        tclsh "%SCRIPT_DIR%device_runner.tcl" --xsdb-path "%XSDB_PATH%" --jtag-tcp "%JTAG_TCP%" %*
    ) else (
        tclsh "%SCRIPT_DIR%device_runner.tcl" --xsdb-path "%XSDB_PATH%" %*
    )
) else (
    if not "%JTAG_TCP%"=="" (
        tclsh "%SCRIPT_DIR%device_runner.tcl" --jtag-tcp "%JTAG_TCP%" %*
    ) else (
        tclsh "%SCRIPT_DIR%device_runner.tcl" %*
    )
)

echo.
echo Device Runner has exited.
pause
