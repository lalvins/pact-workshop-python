PROVIDER_DIR = product-provider-service
CONSUMER_DIR = product-consumer-service
PYTHON       = python3

.PHONY: install install-provider install-consumer install-provider-dev \
        start start-provider start-provider-pact start-consumer \
        test-contract test-provider-verification \
        docker-build docker-start docker-stop docker-clean \
        docker-test-contract docker-test-provider-verification \
        clean clean-all

# ── install (local) ────────────────────────────────────────────────────────────

install: install-provider-dev install-consumer

install-provider:
	@echo "Creating provider venv and installing dependencies..."
	cd $(PROVIDER_DIR) && $(PYTHON) -m venv .venv
	cd $(PROVIDER_DIR) && .venv/bin/pip install --quiet --upgrade pip
	cd $(PROVIDER_DIR) && .venv/bin/pip install fastapi "uvicorn[standard]"

install-provider-dev: install-provider
	@echo "Installing provider dev dependencies (pact-python, pytest)..."
	cd $(PROVIDER_DIR) && .venv/bin/pip install "pact-python>=2.2.0,<3.0.0" pytest

install-consumer:
	@echo "Creating consumer venv and installing dependencies..."
	cd $(CONSUMER_DIR) && $(PYTHON) -m venv .venv
	cd $(CONSUMER_DIR) && .venv/bin/pip install --quiet --upgrade pip
	cd $(CONSUMER_DIR) && .venv/bin/pip install fastapi "uvicorn[standard]" httpx
	cd $(CONSUMER_DIR) && .venv/bin/pip install "pact-python>=2.2.0,<3.0.0" pytest

# ── run (local) ───────────────────────────────────────────────────────────────

start-provider:
	@echo "Starting Product Provider (SQLite mode) on http://localhost:3001"
	cd $(PROVIDER_DIR) && PYTHONPATH=src .venv/bin/python src/api/server.py

start-provider-pact:
	@echo "Starting Product Provider (InMemory / Pact mode) on http://localhost:3001"
	cd $(PROVIDER_DIR) && PYTHONPATH=src:tests/provider .venv/bin/python tests/provider/app_runner.py

start-consumer:
	@echo "Starting Product Consumer on http://localhost:3000"
	cd $(CONSUMER_DIR) && PYTHONPATH=src .venv/bin/python src/api/server.py

start:
	@$(MAKE) start-provider & $(MAKE) start-consumer & wait

# ── test (local) ──────────────────────────────────────────────────────────────

test-contract:
	@echo "Running Pact consumer contract tests (generates pact file)..."
	cd $(CONSUMER_DIR) && PYTHONPATH=src .venv/bin/pytest tests/contract -v

test-provider-verification:
	@echo "Running Pact provider verification..."
	cd $(PROVIDER_DIR) && PYTHONPATH=src:tests/provider .venv/bin/pytest tests/provider -v

# ── docker ────────────────────────────────────────────────────────────────────

docker-build:
	@echo "Building Docker images..."
	docker compose build

docker-start:
	@echo "Starting services via Docker..."
	@touch products.db
	docker compose up

docker-stop:
	docker compose down

docker-clean:
	@echo "Removing Docker images..."
	docker compose down --rmi all

docker-test-contract:
	@echo "Running consumer contract tests in Docker (generates pact file)..."
	@mkdir -p pacts
	docker compose run --rm --no-deps consumer pytest tests/contract -v

docker-test-provider-verification:
	@echo "Running provider verification tests in Docker..."
	docker compose run --rm --no-deps provider \
	  sh -c "PYTHONPATH=/workspace/product-provider-service/src:/workspace/product-provider-service/tests/provider pytest tests/provider -v"