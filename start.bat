@echo off
REM ──────────────────────────────────────────────
REM  HealthAI – Start both servers (Windows)
REM  Run from the project root: start.bat
REM ──────────────────────────────────────────────

echo Starting HealthAI API (FastAPI) on port 8000...
start "HealthAI-API" cmd /k "uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo Starting HealthAI UI (Streamlit) on port 8501...
start "HealthAI-UI" cmd /k "streamlit run ui/app.py --server.port 8501"

echo.
echo ✅  HealthAI is starting up!
echo    API:  http://127.0.0.1:8000
echo    UI:   http://localhost:8501
echo    Docs: http://127.0.0.1:8000/docs
echo.
pause
