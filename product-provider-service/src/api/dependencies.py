from adapters.sqlite_product_repository import SQLiteProductRepository
from ports.product_repository_port import ProductRepositoryPort


def get_repository() -> ProductRepositoryPort:
    """Default DI factory — always returns the real SQLite repository."""
    return SQLiteProductRepository()
