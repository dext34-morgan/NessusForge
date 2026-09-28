@echo off
setlocal EnableExtensions

set "TOOL_NAME=nessusforge"
set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%LOCALAPPDATA%\NessusForge"
set "BIN_DIR=%USERPROFILE%\bin"
set "LAUNCHER=%BIN_DIR%\nessusforge.cmd"

echo.
echo ========================================
echo        NessusForge Installation
echo ========================================
echo.

REM ========================================
REM Check Python
REM ========================================

echo [*] Checking Python...

where python >nul 2>&1

if errorlevel 1 (
    echo [!] Python was not found in PATH.
    echo [!] Install Python 3.9+ and enable:
    echo     "Add Python to PATH"
    exit /b 1
)

python --version

REM ========================================
REM Check project files
REM ========================================

echo.
echo [*] Checking project files...

if not exist "%SCRIPT_DIR%main.py" (
    echo [!] main.py not found.
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

echo [+] Project files found.

REM ========================================
REM Create bin directory
REM ========================================

echo.
echo [*] Creating launcher directory...

if not exist "%BIN_DIR%" (
    mkdir "%BIN_DIR%"
)

REM ========================================
REM Remove old junction
REM ========================================

echo.
echo [*] Checking existing installation...

if exist "%INSTALL_DIR%" (

    echo [!] Existing installation found:
    echo     %INSTALL_DIR%

    fsutil reparsepoint query "%INSTALL_DIR%" >nul 2>&1

    if not errorlevel 1 (

        echo [*] Existing installation is a junction.
        echo [*] Removing old junction...

        rmdir "%INSTALL_DIR%"

        if exist "%INSTALL_DIR%" (
            echo [!] Failed to remove old junction.
            exit /b 1
        )

    ) else (

        echo [!] Existing path is a normal directory.
        echo [!] Please remove or rename it manually:
        echo.
        echo     %INSTALL_DIR%
        echo.
        exit /b 1
    )
)

REM ========================================
REM Create junction
REM ========================================

echo.
echo [*] Creating tool directory junction...

mklink /J "%INSTALL_DIR%" "%SCRIPT_DIR%"

if errorlevel 1 (
    echo [!] Failed to create junction.
    exit /b 1
)

echo [+] Junction created successfully.

REM ========================================
REM Create launcher
REM ========================================

echo.
echo [*] Creating launcher...

> "%LAUNCHER%" echo @echo off
>> "%LAUNCHER%" echo python "%INSTALL_DIR%\main.py" %%*

if not exist "%LAUNCHER%" (
    echo [!] Failed to create launcher.
    exit /b 1
)

echo [+] Launcher created:
echo     %LAUNCHER%

REM ========================================
REM Install dependencies
REM ========================================

echo.
echo [*] Installing Python dependencies...

python -m pip install -r "%INSTALL_DIR%\requirements.txt"

if errorlevel 1 (
    echo.
    echo [!] Failed to install Python dependencies.
    exit /b 1
)

echo [+] Dependencies installed.

REM ========================================
REM Add bin directory to PATH
REM ========================================

echo.
echo [*] Configuring PATH...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$bin='%BIN_DIR%'; $old=[Environment]::GetEnvironmentVariable('Path','User'); if (-not $old) {$old=''}; $parts=$old -split ';' | Where-Object { $_ -ne '' }; if ($parts -notcontains $bin) { $new=($parts + $bin) -join ';'; [Environment]::SetEnvironmentVariable('Path',$new,'User'); Write-Host '[+] Added NessusForge to user PATH.' } else { Write-Host '[+] NessusForge is already in user PATH.' }"

REM ========================================
REM Test launcher
REM ========================================

echo.
echo [*] Testing NessusForge launcher...

call "%LAUNCHER%" --version

if errorlevel 1 (
    echo.
    echo [!] NessusForge launcher test failed.
    echo.
    echo Launcher:
    echo     %LAUNCHER%
    echo.
    echo Main:
    echo     %INSTALL_DIR%\main.py
    exit /b 1
)

REM ========================================
REM Installation complete
REM ========================================

echo.
echo ========================================
echo       Installation completed
echo ========================================
echo.

echo Tool:
echo     nessusforge

echo.
echo Installation:
echo     %INSTALL_DIR%

echo.
echo Launcher:
echo     %LAUNCHER%

echo.
echo IMPORTANT:
echo Close this terminal and open a NEW terminal.
echo.

echo Then run:
echo     nessusforge --version
echo     nessusforge --help
echo     nessusforge
echo.

endlocal
