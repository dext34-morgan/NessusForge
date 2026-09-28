@echo off
setlocal EnableExtensions

set "TOOL_NAME=nessusforge"
set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%USERPROFILE%\NessusForge"
set "BIN_DIR=%USERPROFILE%\bin"
set "LAUNCHER=%BIN_DIR%\%TOOL_NAME%.cmd"

echo.
echo ========================================
echo        NessusForge Installation
echo ========================================
echo.

REM --------------------------------------------------
REM Check required files
REM --------------------------------------------------

if not exist "%SCRIPT_DIR%main.py" (
    echo [!] main.py not found.
    echo     Expected:
    echo     %SCRIPT_DIR%main.py
    exit /b 1
)

if not exist "%SCRIPT_DIR%report.py" (
    echo [!] report.py not found.
    exit /b 1
)

if not exist "%SCRIPT_DIR%requirements.txt" (
    echo [!] requirements.txt not found.
    exit /b 1
)

REM --------------------------------------------------
REM Check Python
REM --------------------------------------------------

echo [*] Checking Python...

where python >nul 2>&1

if errorlevel 1 (
    echo [!] Python was not found in PATH.
    echo [!] Install Python 3.9+ and enable "Add Python to PATH".
    exit /b 1
)

python --version

REM --------------------------------------------------
REM Create bin directory
REM --------------------------------------------------

echo.
echo [*] Creating launcher directory...

if not exist "%BIN_DIR%" (
    mkdir "%BIN_DIR%"
)

REM --------------------------------------------------
REM Remove old NessusForge junction/directory
REM --------------------------------------------------

echo.
echo [*] Checking existing NessusForge installation...

if exist "%INSTALL_DIR%" (

    echo [!] Existing installation found:
    echo     %INSTALL_DIR%
    echo.

    REM Check whether it is a junction
    fsutil reparsepoint query "%INSTALL_DIR%" >nul 2>&1

    if not errorlevel 1 (
        echo [*] Existing installation is a junction.
        echo [*] Removing old junction...

        rmdir "%INSTALL_DIR%" 2>nul

        if exist "%INSTALL_DIR%" (
            echo [!] Could not remove existing junction.
            echo [!] Close programs using NessusForge and run again.
            exit /b 1
        )
    ) else (
        echo [!] Existing installation is a normal directory.
        echo.
        echo [!] The installer will NOT delete it automatically.
        echo.
        echo Choose one:
        echo.
        echo   1. Delete "%INSTALL_DIR%" manually
        echo   2. Rename "%INSTALL_DIR%"
        echo   3. Run this installer again
        echo.
        exit /b 1
    )
)

REM --------------------------------------------------
REM Create directory junction
REM --------------------------------------------------

echo.
echo [*] Creating tool directory junction...

mklink /J "%INSTALL_DIR%" "%SCRIPT_DIR%"

if errorlevel 1 (
    echo.
    echo [!] Failed to create directory junction.
    echo.
    echo Source:
    echo     %SCRIPT_DIR%
    echo.
    echo Destination:
    echo     %INSTALL_DIR%
    echo.
    exit /b 1
)

echo [+] Junction created successfully:
echo.
echo     %INSTALL_DIR%
echo          ^
echo          |
echo     %SCRIPT_DIR%

REM --------------------------------------------------
REM Create launcher
REM --------------------------------------------------

echo.
echo [*] Creating launcher...

(
    echo @echo off
    echo python "%INSTALL_DIR%\main.py" %%*
) > "%LAUNCHER%"

if not exist "%LAUNCHER%" (
    echo [!] Failed to create launcher.
    exit /b 1
)

echo [+] Launcher created:
echo     %LAUNCHER%

REM --------------------------------------------------
REM Install dependencies
REM --------------------------------------------------

echo.
echo [*] Installing Python dependencies...

python -m pip install -r "%INSTALL_DIR%\requirements.txt"

if errorlevel 1 (
    echo.
    echo [!] Failed to install Python dependencies.
    exit /b 1
)

REM --------------------------------------------------
REM Test installation
REM --------------------------------------------------

echo.
echo [*] Testing NessusForge...

call "%LAUNCHER%" --version

if errorlevel 1 (
    echo.
    echo [!] NessusForge installation test failed.
    exit /b 1
)

REM --------------------------------------------------
REM PATH information
REM --------------------------------------------------

echo.
echo ========================================
echo       Installation completed
echo ========================================
echo.

echo Tool:
echo     %TOOL_NAME%

echo.
echo Installation:
echo     %INSTALL_DIR%

echo.
echo Launcher:
echo     %LAUNCHER%

echo.
echo Usage:
echo     nessusforge
echo     nessusforge report.html
echo     nessusforge report.html -pdf report.pdf
echo     nessusforge report.html -pdf report.pdf -o results

echo.
echo Version:
echo     nessusforge --version

echo.
echo NOTE:
echo If "nessusforge" is not recognized, add:
echo.
echo     %BIN_DIR%
echo.
echo to your Windows PATH and open a new terminal.

echo.

endlocal
