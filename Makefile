.PHONY: help up down test lint logs shell-backend redis-cli load-test prewarm build-frontend aws-status aws-up aws-down aws-down-force aws-swap aws-deploy

# Default target
help:
	@echo "================================================================="
	@echo " 🛡️  SpikeShield Management Makefile"
	@echo "================================================================="
	@echo " LOCAL DEVELOPMENT:"
	@echo "   make up              - Start backend, frontend, and redis via Docker"
	@echo "   make down            - Stop local Docker containers"
	@echo "   make test            - Run backend pytest test suite"
	@echo "   make lint            - Run code formatting and linter checks"
	@echo "   make build-frontend  - Build production frontend bundle"
	@echo "   make load-test       - Launch local chaos load test (httpx)"
	@echo "   make prewarm         - Pre-warm local/staging environment"
	@echo ""
	@echo " AWS INFRASTRUCTURE (ap-south-1 Mumbai):"
	@echo "   make aws-status      - View all live EB envs, EC2 instances, ALBs, SQS queues"
	@echo "   make aws-up          - Provision & deploy full AWS stack (Prod + Staging + SQS)"
	@echo "   make aws-down        - Safely terminate all AWS envs & SQS (drops bill to \$$0)"
	@echo "   make aws-down-force  - Terminate AWS envs without confirmation prompt"
	@echo "   make aws-swap        - Execute zero-downtime Blue/Green CNAME swap"
	@echo "   make aws-deploy      - Package and deploy latest code to spikeshield-prod"
	@echo "================================================================="

# Local Development Targets
up:
	docker-compose up --build

down:
	docker-compose down

test:
	cd backend && python -m pytest tests/ -v

lint:
	cd backend && black app/ tests/ && flake8 app/ tests/ --max-line-length=100

logs:
	docker-compose logs -f

shell-backend:
	docker-compose exec backend bash

redis-cli:
	docker-compose exec redis redis-cli

load-test:
	curl -X POST http://localhost:8000/api/v1/chaos/spike -H "Content-Type: application/json" -d "{\"target_url\":\"http://localhost:8000/health\",\"duration_seconds\":30,\"concurrent_users\":50,\"ramp_up_seconds\":5}"

prewarm:
	curl -X POST http://localhost:8000/api/v1/scaling/prewarm -H "Content-Type: application/json" -d "{\"env_name\":\"spikeshield-prod\",\"target_capacity\":4}"

build-frontend:
	cd frontend && npm install && npm run build

# AWS Infrastructure Automation Targets
aws-status:
	python scripts/aws_status.py

aws-up:
	python scripts/aws_up.py

aws-down:
	python scripts/aws_down.py

aws-down-force:
	python scripts/aws_down.py -y

aws-swap:
	python scripts/aws_swap.py

aws-deploy:
	python scratch/deploy_to_eb.py
