from domain.product import Product
from ports.product_service_port import ProductServicePort


class CreateProductUseCase:
    def __init__(self, product_service: ProductServicePort) -> None:
        self._product_service = product_service

    async def execute(self, name: str, price: float) -> Product:
        return await self._product_service.create_product(name, price)