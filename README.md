# Pact Workshop — Python

A hands-on workshop for learning **Consumer-Driven Contract Testing (CDC)** with [Pact](https://docs.pact.io/) and Python.

## What is this?

This repository demonstrates how two microservices can establish a **contract** between them using Pact, so that:

- The **consumer** defines what it expects from the provider (a pact file).
- The **provider** verifies it actually fulfills those expectations.

Both services are built with [FastAPI](https://fastapi.tiangolo.com/) and follow a hexagonal architecture (ports & adapters).

```
┌─────────────────────────────┐          ┌──────────────────────────────┐
│   product-consumer-service  │  HTTP    │   product-provider-service   │
│        (port 3000)          │ ──────►  │        (port 3001)           │
│                             │          │                              │
│  GET /product/{id}          │          │  GET    /products/{id}       │
│                             │          │  POST   /products            │
└─────────────────────────────┘          └──────────────────────────────┘
```

### Contract testing flow

```
1. Consumer tests  →  generate  →  pacts/*.json
2. Provider verification tests  →  verify  →  pacts/*.json against running provider
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | >= 3.11 |
| make | any |
| git | any |

Check your Python version:

```bash
python3 --version
```

---

## Setup

Clone the repository and install all dependencies for both services.

**Option A — uv (recommended):**

```bash
git clone <repository-url>
cd pact-workshop-python
uv sync --all-extras
```

**Option B — make:**

```bash
git clone <repository-url>
cd pact-workshop-python
make install
```

Both options install everything needed to run both services and all tests (`pact-python`, `pytest`, `fastapi`, `uvicorn`, `httpx`).

---

## Running the contract tests

> **No services need to be running before executing the tests.** Both commands are fully self-contained — they manage their own processes internally.

### Step 1 — Consumer contract tests (generates the pact file)

```bash
make test-contract
```

Pact spins up a **mock provider** automatically during the test. There is no need to start the provider service beforehand. On success it writes the contract to:

```
pacts/product-consumer-service-product-provider-service.json
```

### Step 2 — Provider verification (verifies the pact file)

```bash
make test-provider-verification
```

The test harness starts the provider internally in **Pact mode** (in-memory database + state manager), runs the verification, and shuts it down. There is no need to start the provider service beforehand.


### Good news!!!!!
If you reached this point and you have 2 green contract tests for the `make test-contract` command:
```
collected 2 items                                                                                                                                                             
tests/contract/test_get_product_pact.py::TestProductServiceHttpAdapterPactContract::test_returns_product_domain_object_when_provider_responds PASSED                    [ 50%]
tests/contract/test_get_product_pact.py::TestProductServiceHttpAdapterPactContract::test_creates_product_when_provider_accepts_post PASSED                              [100%]

============================================================================== 2 passed in 0.79s ==============================================================================
```

and 1 for the `make test-provider-verification`:

```
collected 1 item                                                                                                                                                              

tests/provider/test_provider_verification.py::TestProviderVerification::test_provider_honours_contract_with_consumer PASSED                                             [100%]

============================================================================== 1 passed in 2.45s ==============================================================================
```

then you are ready to do the exercises!

---

## Experimenting with the services (optional)

If you want to explore the APIs manually using `curl` or Postman, you can start the services:

```bash
make start          # starts both provider (port 3001) and consumer (port 3000)
```

Or individually:

```bash
make start-provider   # provider with SQLite, persists data in products.db
make start-consumer   # consumer, connects to http://localhost:3001
```

Then try:

```bash
curl http://localhost:3000/product/1
```

This is purely optional and has no effect on the contract tests.

---

## Docker (alternative)

If you prefer not to install Python locally, Docker is available as an alternative.

```bash
make docker-build                       # build images — rerun when pyproject.toml changes
make docker-start                       # start both services (auto-reloads on src/ changes)
make docker-test-contract               # run consumer tests → generates pact file
make docker-test-provider-verification  # run provider verification (requires pact file above)
make docker-stop                        # stop containers
make docker-clean                       # stop containers and remove images
```

> Run `docker-test-contract` before `docker-test-provider-verification` — the pact file must exist first.

> `src/` changes are picked up automatically without a rebuild. Only `pyproject.toml` changes require `make docker-build`.

> Consumer and provider services communicate via Docker's internal network — no extra configuration needed.

---

## Project structure

```
pact-workshop-python/
├── Makefile
├── docker-compose.yml
├── pyproject.toml                     # UV workspace config
├── pacts/                             # Generated pact contracts
├── product-consumer-service/
│   ├── Dockerfile
│   ├── src/
│   │   ├── api/                       # FastAPI routes (port 3000)
│   │   ├── adapters/                  # HTTP adapter calling the provider
│   │   ├── application/               # Use cases
│   │   ├── domain/                    # Product domain model
│   │   └── ports/                     # Abstract interface
│   └── tests/
│       └── contract/                  # Pact consumer tests
└── product-provider-service/
    ├── Dockerfile
    ├── src/
    │   ├── api/                       # FastAPI routes (port 3001)
    │   ├── adapters/                  # SQLite & in-memory repositories
    │   ├── domain/                    # Product domain model
    │   └── ports/                     # Abstract interface
    └── tests/
        └── provider/                  # Pact provider verification tests
            ├── app_runner.py          # Starts provider in Pact mode
            └── state_manager.py       # Handles Pact provider states
```

---

## Make targets reference

| Target | Description |
|--------|-------------|
| `make install` | Install dependencies for both services (pip) |
| `make install-provider-dev` | Install provider + dev dependencies (pact, pytest) |
| `make start` | Start provider and consumer in parallel (local) |
| `make start-provider` | Start provider in SQLite mode (port 3001) |
| `make start-provider-pact` | Start provider in Pact/in-memory mode (port 3001) |
| `make start-consumer` | Start consumer (port 3000) |
| `make test-contract` | Run consumer contract tests → generates pact file |
| `make test-provider-verification` | Run provider verification against pact file |
| `make docker-build` | Build Docker images for both services |
| `make docker-start` | Start both services via Docker |
| `make docker-stop` | Stop and remove Docker containers |
| `make docker-clean` | Stop containers and remove images |
| `make docker-test-contract` | Run consumer contract tests in Docker |
| `make docker-test-provider-verification` | Run provider verification in Docker |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `pact.v3` import error | Ensure `pact-python>=2.2.0,<3.0.0` is installed — run `make install` |
| Port 3000 / 3001 already in use | Kill the process: `lsof -ti:3001 \| xargs kill` |
| Provider verification fails with "pact file not found" | Run `make test-contract` first — the pact JSON must exist before verification |
| `/_pact/provider_states` returns 404 on `make start` | `make start` runs production mode (SQLite). Use `make start-provider-pact` for Pact mode |
| `docker compose` not found | Upgrade to Docker Desktop ≥ 4.x (ships Compose v2 as a plugin) |
| Provider fails to start — missing `products.db` | Run `touch products.db` in the repo root before `docker compose up` (handled automatically by `make docker-start`) |
| Docker image build fails downloading pact-python | `pact-python >= 2.2.0` fetches a Rust FFI binary (~50 MB). Retry on a stable connection |
