@echo off
REM Builds and runs the full stack (API + Redis) via Docker Compose.
REM Requires Docker Desktop running. Usage: run_docker.bat [up|down|logs]

setlocal

if not exist ".env" (
    echo No .env found - copying from .env.example. Edit it to add your ANTHROPIC_API_KEY.
    copy .env.example .env
)

set ACTION=%1
if "%ACTION%"=="" set ACTION=up

if "%ACTION%"=="up" (
    docker compose -f docker\docker-compose.yml up --build
) else if "%ACTION%"=="down" (
    docker compose -f docker\docker-compose.yml down
) else if "%ACTION%"=="logs" (
    docker compose -f docker\docker-compose.yml logs -f
) else (
    echo Unknown action: %ACTION%
    echo Usage: run_docker.bat [up|down|logs]
)

endlocal
