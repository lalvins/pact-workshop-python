from domain.product import Product
from ports.product_service_port import ProductServicePort


class GetProductUseCase:
    def __init__(self, product_service_port: ProductServicePort) -> None:
        self._port = product_service_port

    async def execute(self, product_id: str) -> Product:
        return await self._port.get_product(product_id)
