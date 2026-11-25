@echo off
setlocal
cd /d "%~dp0"
title HAYBAT AL SULTAN PRO - Unified Control Center

:MENU
cls
echo ==============================================================================
echo             HAYBAT AL SULTAN PRO - Unified Control Center
echo      Luxury Rosaries, Exhibition POS, Custody & Workshop ERP Platform
echo ==============================================================================
echo.
echo   [1] Start Development Environment (React 19 + Express Server on Port 3001)
echo   [2] Build Production Bundle (Vite Build -^> dist/)
echo   [3] Start Production Server (Node Server on http://localhost:3001)
echo   [4] Launch Desktop Application (Electron Desktop App)
echo   [5] Install Packages ^& Dependencies (npm install)
echo   [6] Run Comprehensive Test Suite (npm test)
echo   [7] Push Direct to GitHub (Clean Push)
echo   [0] Exit
echo.
echo ==============================================================================
set /p "CHOICE=Enter your choice [0-7]: "

if "%CHOICE%"=="1" (
    cls
    echo [INFO] Starting dual development environment...
    npm run dev
    pause
    goto MENU
)

if "%CHOICE%"=="2" (
    cls
    echo [INFO] Building production bundle via Vite...
    npm run build
    echo.
    echo [SUCCESS] Production build completed successfully!
    pause
    goto MENU
)

if "%CHOICE%"=="3" (
    cls
    echo [INFO] Starting production server on http://localhost:3001 ...
    node server_libsql.cjs
    pause
    goto MENU
)

if "%CHOICE%"=="4" (
    cls
    echo [INFO] Launching Electron desktop application...
    npm run electron:start
    pause
    goto MENU
)

if "%CHOICE%"=="5" (
    cls
    echo [INFO] Installing packages and dependencies...
    npm install --legacy-peer-deps
    pause
    goto MENU
)

if "%CHOICE%"=="6" (
    cls
    echo [INFO] Running comprehensive test suite...
    npm test
    pause
    goto MENU
)

if "%CHOICE%"=="7" (
    cls
    call push_to_github.bat
    goto MENU
)

if "%CHOICE%"=="0" exit /b 0

goto MENU
