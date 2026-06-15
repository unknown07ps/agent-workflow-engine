@echo off
REM Runs the FastAPI server locally with uvicorn (requires a local Redis
REM reachable at REDIS_URL, default redis://localhost:6379/0).
REM Usage: run_server.bat

setlocal

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

if not exist ".env" (
    echo No .env found - copying from .env.example
    copy .env.example .env
)

uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

endlocal
