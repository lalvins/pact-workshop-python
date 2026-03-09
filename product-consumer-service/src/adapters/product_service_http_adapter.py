import httpx

from domain.product import Product
from domain.product_not_found_error import ProductNotFoundError
from ports.product_service_port import ProductServicePort


class ProductServiceHttpAdapter(ProductServicePort):
    def __init__(self, base_url: str = "http://localhost:3001") -> None:
        self._base_url = base_url.rstrip("/")

    async def get_product(self, product_id: str) -> Product:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._base_url}/products/{product_id}")

        if response.status_code == 404:
            raise ProductNotFoundError(product_id)

        response.raise_for_status()
        data = response.json()
        return Product(id=data["id"], name=data["name"], price=data["price"])
