PROVIDER_DIR = product-provider-service
CONSUMER_DIR = product-consumer-service
PYTHON       = python3

.PHONY: install install-provider install-consumer install-provider-dev \
        start start-provider start-provider-pact start-consumer \
        test-contract test-provider-verification \
        docker-build docker-start docker-stop \
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

# ── docker run (local) ──────────────────────────────────────────────────────────

docker-build:
	@echo "Building Docker images..."
	docker compose build

start:
	@echo "Starting services via Docker..."
	@touch products.db
	docker compose up

docker-stop:
	docker compose down

docker-test-contract:
	@echo "Running consumer contract tests (generates pact file)..."
	@mkdir -p pacts
	docker compose run --rm --no-deps consumer pytest tests/contract -v

docker-test-provider-verification:
	@echo "Running provider verification tests..."
	docker compose run --rm --no-deps provider \
	  sh -c "PYTHONPATH=/workspace/product-provider-service/src:/workspace/product-provider-service/tests/provider pytest tests/provider -v"

test-contract: docker-test-contract

test-provider-verification: docker-test-provider-verification

# ── test (local) ──────────────────────────────────────────────────────────────

local-test-contract:
	@echo "Running Pact consumer contract tests (generates pact file)..."
	cd $(CONSUMER_DIR) && PYTHONPATH=src .venv/bin/pytest tests/contract -v

local-test-provider-verification:
	@echo "Running Pact provider verification..."
	cd $(PROVIDER_DIR) && PYTHONPATH=src:tests/provider .venv/bin/pytest tests/provider -v

# ── clean ─────────────────────────────────────────────────────────────────────

clean:
	@echo "Removing build artifacts..."
	find . -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -not -path "*/.venv/*" -delete 2>/dev/null || true
	rm -f products.db
	rm -f pacts/*.json

clean-all: clean
	@echo "Removing virtual environments..."
	rm -rf $(PROVIDER_DIR)/.venv $(CONSUMER_DIR)/.venv
