"""
Pact verification app runner — Pact-only concern, lives in tests/provider/.

Wires together the three Pact-specific steps:
  1. Create InMemoryProductRepository (deterministic, isolated from SQLite)
  2. Override the default DI so all routes receive the InMemory repository
  3. Mount the state manager at /_pact/provider_states
  4. Start uvicorn

Requires PYTHONPATH=src:tests/provider (set by the Makefile target and by
the test fixture subprocess env).
"""

import uvicorn
from fastapi import FastAPI

from adapters.in_memory_product_repository import InMemoryProductRepository
from api.dependencies import get_repository
from api.server import create_app
from state_manager import create_state_manager_router

PORT = 3001


def create_pact_app() -> FastAPI:
    repository = InMemoryProductRepository()

    app = create_app()

    # 1. Inject InMemory repository for all routes
    app.dependency_overrides[get_repository] = lambda: repository

    # 2. Mount the state manager so the Pact verifier can POST provider states
    app.include_router(create_state_manager_router(repository))

    return app


if __name__ == "__main__":
    print(f"Product Provider (Pact mode — InMemory) running on http://localhost:{PORT}")
    print(f"  State handler: http://localhost:{PORT}/_pact/provider_states")
    uvicorn.run(create_pact_app(), host="0.0.0.0", port=PORT, log_level="warning")
