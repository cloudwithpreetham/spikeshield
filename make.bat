@echo off
REM SpikeShield Windows Make Shim
if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="status" goto status
if "%1"=="aws-status" goto status
if "%1"=="up" goto aws_up
if "%1"=="aws-up" goto aws_up
if "%1"=="down" goto aws_down
if "%1"=="aws-down" goto aws_down
if "%1"=="aws-down-force" goto aws_down_force
if "%1"=="swap" goto aws_swap
if "%1"=="aws-swap" goto aws_swap
if "%1"=="test" goto test
if "%1"=="build-frontend" goto frontend

echo Unknown command: %1
goto help

:status
python scripts\aws_status.py
goto end

:aws_up
python scripts\aws_up.py
goto end

:aws_down
python scripts\aws_down.py %2
goto end

:aws_down_force
python scripts\aws_down.py -y
goto end

:aws_swap
python scripts\aws_swap.py
goto end

:test
cd backend && pytest tests/ -v && cd ..
goto end

:frontend
cd frontend && npm run build && cd ..
goto end

:help
echo =================================================================
echo  Shield SpikeShield Windows CLI Shim
echo =================================================================
echo   make status        - View live AWS infrastructure status
echo   make up            - Provision and deploy full AWS stack
echo   make down          - Safely tear down AWS infrastructure ($0 bill)
echo   make down -y       - Teardown without confirmation prompt
echo   make swap          - Blue/Green CNAME swap
echo   make test          - Run backend tests
echo   make build-frontend - Build frontend production assets
echo =================================================================
goto end

:end
