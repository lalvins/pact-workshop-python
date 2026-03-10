from abc import ABC, abstractmethod

from domain.product import Product


class ProductServicePort(ABC):
    @abstractmethod
    async def get_product(self, product_id: str) -> Product:
        raise NotImplementedError("ProductServicePort.get_product() is not implemented")

    @abstractmethod
    async def create_product(self, name: str, price: float) -> Product:
        raise NotImplementedError("ProductServicePort.create_product() is not implemented")
