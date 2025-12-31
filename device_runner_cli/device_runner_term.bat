@echo off

rem Launch Tera Term with the appropriate configuration file    
rem and connect to the specified host and port
"%TT_PATH%\\ttermpro.exe" /f=%~dp0\tt_jtag_uart.ini telnet://%1:%2

rem Exit the batch file
exit /b
