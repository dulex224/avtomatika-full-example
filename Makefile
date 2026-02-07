.PHONY: up down restart ps logs clean client health test

# Start the entire stack in the background
up:
	docker compose up --build -d
	@echo "🚀 Stack is starting. Use 'make health' to check when it's ready."

# Stop the stack
down:
	docker compose down

# Restart the stack
restart: down up

# Check container status
ps:
	docker compose ps

# Follow logs of the orchestrator
logs:
	docker compose logs -f orchestrator

# Full cleanup including volumes and databases
clean:
	docker compose down -v
	rm -f avtomatika_history.db
	@echo "🧹 Environment cleaned."

# Run the test client
client:
	python3 client.py

# Run workers locally (requires environment variables set)
worker-gpu:
	python3 workers/gpu.py

worker-cpu-reliable:
	python3 workers/cpu_reliable.py

worker-cpu-unreliable:
	python3 workers/cpu_unreliable.py

# Check system readiness
health:
	@echo "🔍 Checking Orchestrator..."
	@curl -s --fail http://localhost:8080/_public/status || (echo "❌ Orchestrator is not running" && exit 1)
	@echo "🔍 Checking Workers Registration..."
	@curl -s -H "X-Client-Token: user_token_vip" http://localhost:8080/api/v1/workers | grep -q "worker_id" || (echo "❌ No workers registered" && exit 1)
	@echo "✅ System is UP and READY"

# Generate visual graphs of the blueprints (requires graphviz)
graph:
	python3 generate_graphs.py

# Run linter (ruff)
lint:
	ruff check .
	ruff format --check .

# Run integration tests
test:
	pytest -s tests/
