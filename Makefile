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
	curl -X POST http://localhost:8000/api/v1/chaos/spike -H 'Content-Type: application/json' -d '{"target_url":"http://localhost:8000/health","duration_seconds":30,"concurrent_users":50,"ramp_up_seconds":5}'

prewarm:
	curl -X POST http://localhost:8000/api/v1/scaling/prewarm -H 'Content-Type: application/json' -d '{"env_name":"spikeshield-prod","target_capacity":10}'

build-frontend:
	cd frontend && npm install && npm run build
