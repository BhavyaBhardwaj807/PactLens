@echo off
REM PactLens Setup Script for Windows

echo.
echo PactLens Setup
echo ==============
echo.

REM Check Python
echo Checking Python...
python --version

REM Setup Backend
echo.
echo Setting up Backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Backend dependencies installed

REM Create .env
if not exist .env (
    copy .env.example .env
    echo Created .env file
    echo   WARNING: Please edit .env and add your OpenAI API key
)

cd ..

REM Setup Frontend
echo.
echo Setting up Frontend...
cd frontend
call npm install
echo Frontend dependencies installed

cd ..

echo.
echo Setup Complete!
echo.
echo Next steps:
echo 1. Edit backend\.env with your OpenAI API key
echo 2. Run backend: cd backend ^&^& venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload
echo 3. Run frontend: cd frontend ^&^& npm run dev
echo 4. Open http://localhost:5173
