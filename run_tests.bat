@echo off
REM Runs the test suite. Usage: run_tests.bat [extra pytest args]

setlocal

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

set PYTHONPATH=.
python -m pytest %*

endlocal
