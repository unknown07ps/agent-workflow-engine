@echo off
REM Creates a virtual environment and installs dependencies (incl. dev/test deps).
REM Usage: setup.bat

setlocal

if not exist ".venv" (
    echo ^>^> Creating virtual environment in .venv
    python -m venv .venv
)

echo ^>^> Activating virtual environment
call .venv\Scripts\activate.bat

echo ^>^> Installing dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

if not exist ".env" (
    echo ^>^> Creating .env from .env.example - edit it to add your ANTHROPIC_API_KEY
    copy .env.example .env
)

echo.
echo Setup complete. Activate the venv with: .venv\Scripts\activate.bat
echo Then run tests with: run_tests.bat
echo Or start the API with: run_server.bat

endlocal
