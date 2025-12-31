@echo off
title Device Runner CLI
echo ========================================
echo    Device Runner CLI v1.0.0 - Windows
echo ========================================
echo.

rem Uncomment below to automatically start hardware server on local machine
rem tasklist | findstr /i "hw_server.exe" >nul && goto LAUNCH_DEVICE_RUNNER_CLI
rem echo Starting Hardware Server...
rem start /b %HW_SERVER_PATH%/hw_server.bat"
rem :L

echo Starting Device Runner CLI via XSDB...
echo.

%XSDB_PATH%\xsdb device_runner_cli.tcl ^
        -arch zynqMP ^
        -mode user ^
        -hw_server localhost ^
        -ps_ref_clk 0 ^
        -term_app device_runner_term.bat ^
        -log_dir logs ^
        -bit_file bin\kv260_design.bit ^
        -fsbl_path bin\fsbl.elf


