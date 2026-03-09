from abc import ABC, abstractmethod
from typing import Optional

from domain.product import Product


class ProductRepositoryPort(ABC):
    @abstractmethod
    async def get_all(self) -> list[Product]:
        raise NotImplementedError("ProductRepositoryPort.get_all() is not implemented")

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Product]:
        raise NotImplementedError("ProductRepositoryPort.get_by_id() is not implemented")

    @abstractmethod
    async def create(self, name: str, price: float) -> Product:
        raise NotImplementedError("ProductRepositoryPort.create() is not implemented")

    @abstractmethod
    async def update(self, id: str, name: str, price: float) -> Optional[Product]:
        raise NotImplementedError("ProductRepositoryPort.update() is not implemented")

    @abstractmethod
    async def delete(self, id: str) -> bool:
        raise NotImplementedError("ProductRepositoryPort.delete() is not implemented")
