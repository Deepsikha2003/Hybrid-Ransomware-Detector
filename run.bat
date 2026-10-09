@echo off
setlocal
cd /d "%~dp0"
title Hybrid Ransomware Detection System
echo ==============================================
echo  Hybrid Ransomware Detection System
echo ==============================================

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 - 3.12 and tick "Add Python to PATH".
  pause
  exit /b 1
)

if not exist backend\.venv\Scripts\activate.bat (
  echo [1/4] Creating Python environment...
  python -m venv backend\.venv
  if errorlevel 1 goto :fail
)
call backend\.venv\Scripts\activate.bat

if not exist backend\.venv\deps_ok.txt (
  echo [2/4] Installing Python packages. First run only, takes a few minutes...
  python -m pip install --upgrade pip
  python -m pip install -r backend\requirements.txt
  if errorlevel 1 goto :fail
  echo ok> backend\.venv\deps_ok.txt
)

if not exist backend\models\static_xgb.joblib (
  echo [3/4] Training DEMO models on synthetic data...
  pushd backend
  python -m app.ml.train --demo
  if errorlevel 1 goto :fail
  popd
)

if not exist frontend\dist\index.html (
  echo [4/4] Building the website. First run only...
  where npm >nul 2>nul
  if errorlevel 1 (
    echo Node.js was not found. Install the LTS version from nodejs.org, then run this again.
    pause
    exit /b 1
  )
  pushd frontend
  call npm install
  if errorlevel 1 goto :fail
  call npm run build
  if errorlevel 1 goto :fail
  popd
)

echo.
echo  Starting... the browser opens at http://localhost:8000
echo  Login:  admin@example.com   /   ChangeMe!12345
echo  Close this window to stop the app.
echo.
start "" cmd /c "timeout /t 5 >nul & start http://localhost:8000"
cd backend
python -m uvicorn app.main:app --port 8000
goto :eof

:fail
echo.
echo Something went wrong. Copy the red/error text above and send it to me.
pause
exit /b 1
