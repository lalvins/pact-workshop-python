from typing import Optional

from domain.product import Product
from ports.product_repository_port import ProductRepositoryPort


class InMemoryProductRepository(ProductRepositoryPort):
    def __init__(self) -> None:
        self._store: dict[str, Product] = {
            "1": Product(id="1", name="Coffee Mug", price=12.99),
            "2": Product(id="2", name="Laptop Stand", price=45.00),
        }
        self._next_id = 3

    async def get_all(self) -> list[Product]:
        return list(self._store.values())

    async def get_by_id(self, id: str) -> Optional[Product]:
        return self._store.get(str(id))

    async def create(self, name: str, price: float) -> Product:
        id = str(self._next_id)
        self._next_id += 1
        product = Product(id=id, name=name, price=price)
        self._store[id] = product
        return product

    async def update(self, id: str, name: str, price: float) -> Optional[Product]:
        if str(id) not in self._store:
            return None
        product = Product(id=str(id), name=name, price=price)
        self._store[str(id)] = product
        return product

    async def delete(self, id: str) -> bool:
        if str(id) in self._store:
            del self._store[str(id)]
            return True
        return False
