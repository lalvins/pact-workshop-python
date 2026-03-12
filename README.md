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

- [Docker](https://docs.docker.com/get-docker/) (includes Docker Compose v2)
- `make`
- `git`

> **Local Python alternative:** If you prefer running without Docker, you need Python 3.11+ and can use `make install` followed by `make local-test-contract` and `make local-test-provider-verification`.

---

## Setup

Clone the repository and build the Docker images:

```bash
git clone <repository-url>
cd pact-workshop-python
make docker-build
```

> First build takes ~2 minutes — pact-python downloads a Rust FFI binary (~50 MB).

---

## Running the contract tests

> Tests run inside Docker containers. No local Python installation needed.
> No services need to be running before executing the tests.

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

---

## Experimenting with the services (optional)

If you want to explore the APIs manually using `curl` or Postman, you can start the services as Docker containers:

```bash
make start          # starts both provider (port 3001) and consumer (port 3000) via Docker
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

## Project structure

```
pact-workshop-python/
├── Makefile
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
| `make docker-build` | Build Docker images for both services |
| `make start` | Start both services via Docker (ports 3000, 3001) |
| `make docker-stop` | Stop and remove Docker containers |
| `make test-contract` | Run consumer contract tests in Docker → generates pact file |
| `make test-provider-verification` | Run provider verification in Docker against pact file |
| `make local-test-contract` | Run consumer tests locally (requires `make install` first) |
| `make local-test-provider-verification` | Run provider verification locally (requires `make install` first) |
| `make install` | Install local venv dependencies (optional, for local dev) |
| `make clean` | Remove __pycache__, products.db, pact files |
| `make clean-all` | Remove everything including .venv directories |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker compose` not found | Upgrade to Docker Desktop ≥ 4.x (ships Compose v2 as a plugin) |
| Port 3000 / 3001 already in use | `make docker-stop` or kill the local process: `lsof -ti:3001 \| xargs kill` |
| Provider verification fails with "pact file not found" | Run `make test-contract` first — the pact JSON must exist before verification |
| `/_pact/provider_states` returns 404 on `make start` | `make start` runs production mode (SQLite). Use `docker compose run --rm provider python tests/provider/app_runner.py` for Pact mode |
| Image build fails downloading pact-python | `pact-python >= 2.2.0` fetches a Rust FFI binary (~50 MB). Retry on a stable connection |
