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

:: 3. Configure Local Git Identity (Account Isolation)
echo ------------------------------------------------------------------------------
echo [1/4] GITHUB ACCOUNT AND IDENTITY CONFIGURATION
echo ------------------------------------------------------------------------------
echo Since you are using a different GitHub account, we configure it LOCALLY
echo for this repository only, without modifying your global computer settings.
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

:: 4. Configure Remote Repository URL
echo ------------------------------------------------------------------------------
echo [2/4] GITHUB REPOSITORY CONFIGURATION
echo ------------------------------------------------------------------------------

set "CURRENT_REMOTE="
for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set "CURRENT_REMOTE=%%i"

if defined CURRENT_REMOTE (
    echo Current remote repository URL:
    echo   !CURRENT_REMOTE!
    echo.
    set /p "KEEP_REMOTE=Do you want to push to this repository? [Y/N] (Default: Y): "
    if /i "!KEEP_REMOTE!"=="N" (
        set "CURRENT_REMOTE="
    )
)

if not defined CURRENT_REMOTE (
    echo.
    echo Please enter your target GitHub repository URL.
    echo Example HTTPS: https://github.com/your-username/your-repo.git
    echo Example SSH  : git@github.com:your-username/your-repo.git
    echo.
    set /p "REPO_URL=Target Repository URL: "
    
    if "!REPO_URL!"=="" (
        echo [ERROR] Repository URL cannot be empty.
        echo.
        pause
        exit /b 1
    )
    
    git remote remove origin >nul 2>&1
    git remote add origin !REPO_URL!
    echo [OK] Remote 'origin' configured to: !REPO_URL!
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

:: 6. Commit Message
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
echo [*] Staging all files (git add .) ...
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
echo NOTE: If GitHub asks for credentials, enter your GitHub Username and 
echo Personal Access Token (PAT) as the password.
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
echo [WARNING] Direct push was rejected by GitHub.
echo ==============================================================================
echo This typically happens if the remote GitHub repository already contains files 
echo (such as a README, license, or previous commits) that are not in this local copy.
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
