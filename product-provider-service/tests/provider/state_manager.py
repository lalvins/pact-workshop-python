"""
Pact provider state manager — Pact-only concern, lives in tests/provider/.

create_state_manager_router(repository) returns a FastAPI APIRouter that
exposes POST /_pact/provider_states. The Pact verifier calls this endpoint
before each interaction to set up the required provider state.

The repository is received by argument (plain closure), so no DI framework
is needed here.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ports.product_repository_port import ProductRepositoryPort


class ProviderStateBody(BaseModel):
    state: str
    action: Optional[str] = "setup"
    params: Optional[dict] = None


def create_state_manager_router(repository: ProductRepositoryPort) -> APIRouter:
    router = APIRouter()

    @router.post("/_pact/provider_states", status_code=200)
    async def set_provider_state(body: ProviderStateBody):
        if body.action in ("setup", None):
            await _setup(body.state, repository)
        elif body.action == "teardown":
            await _teardown(body.state, repository)
        return {"state": body.state, "action": body.action}

    return router


async def _setup(state: str, repository: ProductRepositoryPort) -> None:
    if state == "product with id 1 exists":
        # InMemoryProductRepository is pre-seeded with products 1 & 2 — no action needed.
        pass

    # Add future state handlers here, e.g.:
    # elif state == "no products exist":
    #     for product in await repository.get_all():
    #         await repository.delete(product.id)


async def _teardown(state: str, repository: ProductRepositoryPort) -> None:
    pass
