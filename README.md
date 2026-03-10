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

Clone the repository and install all dependencies for both services:

```bash
git clone <repository-url>
cd pact-workshop-python
make install
```

This creates a `.venv` inside each service directory and installs all required packages (including `pact-python`, `pytest`, `fastapi`, `uvicorn`, and `httpx`).

For provider dev dependencies (required for running provider verification tests), run:

```bash
make install-provider-dev
```

> `make install` already covers the consumer. `install-provider-dev` adds `pact-python` and `pytest` to the provider's environment on top of the base install.

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

## Project structure

```
pact-workshop-python/
├── Makefile
├── pyproject.toml                     # UV workspace config
├── pacts/                             # Generated pact contracts
├── product-consumer-service/
│   ├── src/
│   │   ├── api/                       # FastAPI routes (port 3000)
│   │   ├── adapters/                  # HTTP adapter calling the provider
│   │   ├── application/               # Use cases
│   │   ├── domain/                    # Product domain model
│   │   └── ports/                     # Abstract interface
│   └── tests/
│       └── contract/                  # Pact consumer tests
└── product-provider-service/
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
| `make install` | Install dependencies for both services |
| `make install-provider-dev` | Install provider + dev dependencies (pact, pytest) |
| `make start` | Start provider and consumer in parallel |
| `make start-provider` | Start provider in SQLite mode (port 3001) |
| `make start-provider-pact` | Start provider in Pact/in-memory mode (port 3001) |
| `make start-consumer` | Start consumer (port 3000) |
| `make test-contract` | Run consumer contract tests → generates pact file |
| `make test-provider-verification` | Run provider verification against pact file |
