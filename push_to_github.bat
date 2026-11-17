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

:: Disable global credential helper locally to avoid using old cached account
git config --local credential.helper ""

:: 3. Configure Local Git Identity
echo ------------------------------------------------------------------------------
echo [1/4] GITHUB ACCOUNT AND IDENTITY CONFIGURATION
echo ------------------------------------------------------------------------------
echo Setting your Git author name and email LOCALLY for this repository only.
echo.

set "CURRENT_USER_NAME="
set "CURRENT_USER_EMAIL="

for /f "tokens=*" %%i in ('git config --local user.name 2^>nul') do set "CURRENT_USER_NAME=%%i"
for /f "tokens=*" %%i in ('git config --local user.email 2^>nul') do set "CURRENT_USER_EMAIL=%%i"

if defined CURRENT_USER_NAME (
    echo Current local Git author name  : !CURRENT_USER_NAME!
    echo Current local Git author email : !CURRENT_USER_EMAIL!
    echo.
    set /p "CHANGE_IDENTITY=Do you want to change this Git author identity? [Y/N]: "
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
echo Enter your Personal Access Token (PAT) generated for your GitHub account.
echo.

set "CURRENT_REMOTE="
for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set "CURRENT_REMOTE=%%i"

if defined CURRENT_REMOTE (
    echo Current remote repository configured:
    echo   !CURRENT_REMOTE!
    echo.
    set /p "KEEP_REMOTE=Do you want to reuse this repository? [Y/N]: "
    if /i "!KEEP_REMOTE!"=="N" (
        set "CURRENT_REMOTE="
    )
)

if not defined CURRENT_REMOTE (
    echo.
    echo Please enter your target GitHub repository URL.
    echo Example: https://github.com/haybatalsultan/alsultan.git
    echo.
    set /p "RAW_URL=Target Repository: "
    if "!RAW_URL!"=="" set "RAW_URL=https://github.com/haybatalsultan/alsultan.git"
) else (
    set "RAW_URL=!CURRENT_REMOTE!"
)

echo !RAW_URL! | findstr /i "github.com" >nul
if %ERRORLEVEL% neq 0 (
    set "RAW_URL=https://github.com/!RAW_URL!.git"
)

echo.
echo ------------------------------------------------------------------------------
echo [AUTHENTICATION] PERSONAL ACCESS TOKEN (PAT)
echo ------------------------------------------------------------------------------
echo Paste your GitHub Personal Access Token (PAT).
echo Press [ENTER] without typing to keep current credentials.
echo.
set /p "PAT_TOKEN=Enter your GitHub Personal Access Token (PAT): "

if not "!PAT_TOKEN!"=="" (
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
    if not defined CURRENT_REMOTE (
        git remote remove origin >nul 2>&1
        git remote add origin !RAW_URL!
        echo [OK] Remote configured: !RAW_URL!
    )
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

set "COMMIT_MSG=Deploy Haybat Al Sultan Updates"
echo Enter your commit message describing the changes.
echo Press [ENTER] to use default: "!COMMIT_MSG!"
echo.
set /p "USER_MSG=Commit message: "
if not "!USER_MSG!"=="" set "COMMIT_MSG=!USER_MSG!"

echo.
echo [*] Staging all files including dist (git add .) ...
git add .

echo [*] Committing changes...
git commit -m "!COMMIT_MSG!"
if %ERRORLEVEL% neq 0 (
    echo [INFO] No new unstaged changes, proceeding with existing commits.
) else (
    echo [OK] Commit created successfully.
)
echo.

:: 7. Push to GitHub
echo ------------------------------------------------------------------------------
echo [4/4] PUSHING TO GITHUB
echo ------------------------------------------------------------------------------
echo [*] Pushing branch '!BRANCH!' to GitHub origin...
echo.

git push -u origin !BRANCH!
if %ERRORLEVEL% equ 0 (
    echo.
    echo ==============================================================================
    echo [SUCCESS] All files and updates have been successfully pushed to GitHub!
    echo ==============================================================================
    echo.
    echo Next step: Go to Easypanel and click 'Deploy' or 'Redeploy'.
    echo.
    pause
    exit /b 0
)

:: 8. Error Recovery Handler
echo.
echo ==============================================================================
echo [WARNING] Push failed or was rejected by GitHub.
echo ==============================================================================
echo Options:
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
            echo Next step: Go to Easypanel and click 'Deploy' or 'Redeploy'.
            echo.
            pause
            exit /b 0
        )
    )
    echo [ERROR] Pull or push failed. Please check for merge conflicts.
)

if "!RECOVERY_CHOICE!"=="2" (
    echo.
    echo [!] Force pushing to origin/!BRANCH!...
    git push -u origin !BRANCH! --force
    if %ERRORLEVEL% equ 0 (
        echo.
        echo [SUCCESS] Force push completed successfully!
        echo Next step: Go to Easypanel and click 'Deploy' or 'Redeploy'.
        echo.
        pause
        exit /b 0
    ) else (
        echo [ERROR] Force push failed. Please check permissions or token.
    )
)

echo.
echo Operation paused. Check error messages above.
echo.
pause
exit /b 1
