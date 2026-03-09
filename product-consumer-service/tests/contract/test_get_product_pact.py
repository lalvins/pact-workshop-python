"""
Consumer-driven contract test — mirrors the Node.js Pact workshop.

Requires: pact-python >= 2.2.0  (PactV3 via Rust FFI)
Run with: cd product-consumer-service && PYTHONPATH=src .venv/bin/pytest tests/contract -v
         (or from repo root: make test-contract)
"""

import asyncio
from pathlib import Path

import pytest
from pact.v3 import Pact, match

from adapters.product_service_http_adapter import ProductServiceHttpAdapter
from application.get_product_use_case import GetProductUseCase
from domain.product import Product

PACTS_DIR = Path(__file__).resolve().parents[3] / "pacts"


@pytest.fixture(scope="module")
def pact() -> Pact:
    return Pact(
        consumer="product-consumer-service",
        provider="product-provider-service",
    )


class TestProductServiceHttpAdapterPactContract:
    """
    ProductServiceHttpAdapter — Pact consumer contract

    Data flow under test:
        GetProductUseCase → ProductServiceHttpAdapter → Pact mock server
    """

    def test_returns_product_domain_object_when_provider_responds(
        self, pact: Pact
    ) -> None:
        (
            pact.upon_receiving("a GET request for product with id 1")
            .given("product with id 1 exists")
            .with_request(method="GET", path="/products/1")
            .will_respond_with(200)
            .with_body(
                {
                    "id": match.like("1"),
                    "name": match.like("Coffee Mug"),
                    "price": match.like(12.99),
                },
                content_type="application/json",
            )
        )

        async def _run(base_url: str) -> Product:
            adapter = ProductServiceHttpAdapter(base_url)
            use_case = GetProductUseCase(adapter)
            return await use_case.execute("1")

        with pact.serve() as mock_server:
            product = asyncio.run(_run(str(mock_server.url)))

        pact.write_file(directory=PACTS_DIR, overwrite=True)

        assert isinstance(product, Product)
        assert isinstance(product.id, str)
        assert isinstance(product.name, str)
        assert isinstance(product.price, float)
