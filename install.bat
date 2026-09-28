@echo off
setlocal

set "TOOL_NAME=nessusforge"
set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%USERPROFILE%\%TOOL_NAME%"
set "BIN_DIR=%USERPROFILE%\bin"
set "LAUNCHER=%BIN_DIR%\%TOOL_NAME%.cmd"

echo.
echo ========================================
echo        NessusForge Installation
echo ========================================
echo.

if not exist "%SCRIPT_DIR%main.py" (
    echo [!] main.py not found.
    exit /b 1
)

if not exist "%SCRIPT_DIR%requirements.txt" (
    echo [!] requirements.txt not found.
    exit /b 1
)

echo [*] Creating tool directory...

if exist "%INSTALL_DIR%" (
    rmdir "%INSTALL_DIR%" 2>nul
)

mklink /J "%INSTALL_DIR%" "%SCRIPT_DIR%"

if errorlevel 1 (
    echo [!] Failed to create directory junction.
    exit /b 1
)

echo [+] Junction created:
echo     %INSTALL_DIR% -^> %SCRIPT_DIR%

echo.
echo [*] Creating launcher directory...

if not exist "%BIN_DIR%" (
    mkdir "%BIN_DIR%"
)

echo [*] Creating launcher...

(
    echo @echo off
    echo python "%INSTALL_DIR%\main.py" %%*
) > "%LAUNCHER%"

echo [+] Launcher created:
echo     %LAUNCHER%

echo.
echo [*] Installing Python dependencies...

where python >nul 2>&1

if errorlevel 1 (
    echo [!] Python was not found in PATH.
    echo [!] Install Python and make sure "Add Python to PATH" is enabled.
    exit /b 1
)

python -m pip install -r "%INSTALL_DIR%\requirements.txt"

echo.
echo ========================================
echo       Installation completed
echo ========================================
echo.

echo Tool location:
echo     %INSTALL_DIR%

echo.
echo Usage:
echo     %TOOL_NAME%
echo     %TOOL_NAME% report.html
echo     %TOOL_NAME% report.html -pdf report.pdf
echo     %TOOL_NAME% report.html -pdf report.pdf -o results

echo.
echo Version:
echo     %TOOL_NAME% --version

echo.
echo [!] If "%BIN_DIR%" is not in PATH, add:
echo     %BIN_DIR%

echo.

endlocal