@echo off
setlocal enabledelayedexpansion

title Haybat Al Sultan - GitHub Deployment Tool

echo ==============================================================================
echo              HAYBAT AL SULTAN - GITHUB PUSH AND DEPLOYMENT TOOL
echo ==============================================================================
echo.

:: 1. Check if Git is installed
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not found in your system PATH.
    echo Please download and install Git from: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

:: 2. Initialize Git repository if not present
if not exist ".git" (
    echo [*] Initializing local Git repository...
    git init
    git branch -M main
    echo [OK] Git repository initialized with branch 'main'.
    echo.
) else (
    echo [OK] Local Git repository detected.
    echo.
)

:: Disable global credential helper locally to avoid silently using the wrong Windows cached account
git config --local credential.helper ""

:: 3. Configure Local Git Identity (Account Isolation)
echo ------------------------------------------------------------------------------
echo [1/4] GITHUB ACCOUNT AND IDENTITY CONFIGURATION
echo ------------------------------------------------------------------------------
echo Setting your Git author name and email LOCALLY for this repository only,
echo preventing conflicts with other GitHub accounts on this computer.
echo.

set "CURRENT_USER_NAME="
set "CURRENT_USER_EMAIL="

for /f "tokens=*" %%i in ('git config --local user.name 2^>nul') do set "CURRENT_USER_NAME=%%i"
for /f "tokens=*" %%i in ('git config --local user.email 2^>nul') do set "CURRENT_USER_EMAIL=%%i"

if defined CURRENT_USER_NAME (
    echo Current local Git author name  : !CURRENT_USER_NAME!
    echo Current local Git author email : !CURRENT_USER_EMAIL!
    echo.
    set /p "CHANGE_IDENTITY=Do you want to change this Git author identity? [Y/N] (Default: N): "
    if /i "!CHANGE_IDENTITY!"=="Y" (
        set "CURRENT_USER_NAME="
    )
)

if not defined CURRENT_USER_NAME (
    set /p "GIT_NAME=Enter your GitHub display name or username: "
    set /p "GIT_EMAIL=Enter your GitHub account email address: "
    
    if not "!GIT_NAME!"=="" git config --local user.name "!GIT_NAME!"
    if not "!GIT_EMAIL!"=="" git config --local user.email "!GIT_EMAIL!"
    echo [OK] Local repository identity saved.
)
echo.

:: 4. Configure Remote Repository URL and Authentication Token
echo ------------------------------------------------------------------------------
echo [2/4] GITHUB REPOSITORY AND AUTHENTICATION
echo ------------------------------------------------------------------------------
echo Windows automatically caches credentials for GitHub accounts in Credential Manager.
echo To ensure this project pushes to your NEW account and not the old one,
echo you can enter a Personal Access Token (PAT) generated for your new account.
echo.

set "CURRENT_REMOTE="
for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set "CURRENT_REMOTE=%%i"

if defined CURRENT_REMOTE (
    echo Current remote repository URL:
    echo   !CURRENT_REMOTE!
    echo.
    set /p "KEEP_REMOTE=Do you want to use this repository? [Y/N] (Default: Y): "
    if /i "!KEEP_REMOTE!"=="N" (
        set "CURRENT_REMOTE="
    )
)

if not defined CURRENT_REMOTE (
    echo.
    echo Please enter your target GitHub repository URL or path.
    echo Examples:
    echo   https://github.com/haybatalsultan/alsultan.git
    echo   haybatalsultan/alsultan
    echo.
    set /p "USER_INPUT_URL=Target Repository: "
    
    if "!USER_INPUT_URL!"=="" (
        echo [ERROR] Repository URL cannot be empty.
        pause
        exit /b 1
    )
    set "RAW_URL=!USER_INPUT_URL!"
) else (
    set "RAW_URL=!CURRENT_REMOTE!"
)

:: Normalize URL format
echo !RAW_URL! | findstr /i "github.com" >nul
if %ERRORLEVEL% neq 0 (
    set "RAW_URL=https://github.com/!RAW_URL!.git"
)

:: Ask for Personal Access Token (PAT)
echo.
echo ------------------------------------------------------------------------------
echo [AUTHENTICATION] PERSONAL ACCESS TOKEN (PAT)
echo ------------------------------------------------------------------------------
echo To authenticate directly with your new account (bypassing Windows cached logins):
echo Provide your Personal Access Token (PAT).
echo If you don't have one, generate it at: https://github.com/settings/tokens
echo (Required scope: 'repo' - Full control of private repositories)
echo.
echo Press [ENTER] without typing a token if you prefer Git to prompt in the console.
echo.
set /p "PAT_TOKEN=Enter your GitHub Personal Access Token (PAT): "

if not "!PAT_TOKEN!"=="" (
    :: Strip any existing auth info and prepend token
    for /f "tokens=1,* delims=@" %%a in ("!RAW_URL!") do (
        if "%%b"=="" (
            set "CLEAN_URL=!RAW_URL!"
        ) else (
            set "CLEAN_URL=https://%%b"
        )
    )
    for /f "tokens=1,* delims=/" %%x in ("!CLEAN_URL:https://=!") do (
        set "FINAL_URL=https://!PAT_TOKEN!@%%x/%%y"
    )
    git remote remove origin >nul 2>&1
    git remote add origin !FINAL_URL!
    echo [OK] Remote configured with your custom Personal Access Token.
) else (
    git remote remove origin >nul 2>&1
    git remote add origin !RAW_URL!
    echo [OK] Remote configured: !RAW_URL!
    echo [INFO] Local credential manager disabled. Git will prompt you in console.
)
echo.

:: 5. Determine Current Branch
set "BRANCH=main"
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do (
    if not "%%i"=="" set "BRANCH=%%i"
)
if "!BRANCH!"=="" (
    set "BRANCH=main"
    git branch -M main >nul 2>&1
)

echo Target Branch: !BRANCH!
echo.

:: 6. Staging and Commit
echo ------------------------------------------------------------------------------
echo [3/4] STAGING AND COMMIT MESSAGE
echo ------------------------------------------------------------------------------

for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "CURR_DATE=%%c-%%a-%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "CURR_TIME=%%a:%%b"
set "DEFAULT_MSG=Update Haybat Al Sultan Store - %DATE% %TIME%"

echo Enter your commit message describing the changes.
echo Press [ENTER] to use default: "!DEFAULT_MSG!"
echo.
set /p "USER_MSG=Commit message: "

if "!USER_MSG!"=="" (
    set "COMMIT_MSG=!DEFAULT_MSG!"
) else (
    set "COMMIT_MSG=!USER_MSG!"
)

echo.
echo [*] Checking production frontend build (dist)...
if not exist "dist\index.html" (
    echo [*] dist directory not found. Building now (npm run build)...
    call npm run build
) else (
    set /p "REBUILD_CHOICE=Do you want to re-build the latest frontend before pushing? [Y/N] (Default: Y): "
    if not "!REBUILD_CHOICE!"=="N" if not "!REBUILD_CHOICE!"=="n" (
        echo [*] Compiling production build (npm run build)...
        call npm run build
    )
)

echo.
echo [*] Staging all files including dist (git add .) ...
git add .

echo [*] Committing changes...
git commit -m "!COMMIT_MSG!"
if %ERRORLEVEL% neq 0 (
    echo [INFO] No new changes to commit, or commit already up to date.
) else (
    echo [OK] Commit created successfully.
)
echo.

:: 7. Push to GitHub
echo ------------------------------------------------------------------------------
echo [4/4] PUSHING TO GITHUB
echo ------------------------------------------------------------------------------
echo [*] Pushing branch '!BRANCH!' to origin...
echo.

git push -u origin !BRANCH!
if %ERRORLEVEL% equ 0 (
    echo.
    echo ==============================================================================
    echo [SUCCESS] All files and updates have been successfully pushed to GitHub!
    echo ==============================================================================
    echo.
    pause
    exit /b 0
)

:: 8. Error Recovery Handler
echo.
echo ==============================================================================
echo [WARNING] Push failed or was rejected by GitHub.
echo ==============================================================================
echo Common causes:
echo   1. The repository is private or does not exist under this account.
echo   2. The Personal Access Token (PAT) lacks 'repo' write permissions.
echo   3. The remote repository already contains files (README, license, etc.).
echo.
echo Choose an option to resolve:
echo   [1] Pull and Rebase remote changes, then push (Recommended)
echo   [2] Force push (OVERWRITE remote repository with this local version)
echo   [3] Cancel and exit
echo.
set /p "RECOVERY_CHOICE=Select an option [1, 2, or 3]: "

if "!RECOVERY_CHOICE!"=="1" (
    echo.
    echo [*] Pulling with rebase from origin/!BRANCH!...
    git pull --rebase origin !BRANCH!
    if %ERRORLEVEL% equ 0 (
        echo [*] Re-attempting push...
        git push -u origin !BRANCH!
        if %ERRORLEVEL% equ 0 (
            echo.
            echo [SUCCESS] Rebase and push completed successfully!
            pause
            exit /b 0
        )
    )
    echo [ERROR] Pull or push failed. Please check for merge conflicts.
)

if "!RECOVERY_CHOICE!"=="2" (
    echo.
    echo [!] WARNING: Force pushing will overwrite the remote repository.
    set /p "CONFIRM_FORCE=Are you sure you want to force push? [Y/N]: "
    if /i "!CONFIRM_FORCE!"=="Y" (
        git push -u origin !BRANCH! --force
        if %ERRORLEVEL% equ 0 (
            echo.
            echo [SUCCESS] Force push completed successfully!
            pause
            exit /b 0
        ) else (
            echo [ERROR] Force push failed. Please check permissions or token.
        )
    )
)

echo.
echo Operation cancelled or failed. Please check your credentials and repository settings.
echo.
pause
exit /b 1
