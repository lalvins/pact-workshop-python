import asyncio
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from domain.product import Product
from ports.product_repository_port import ProductRepositoryPort

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "products.db"


class SQLiteProductRepository(ProductRepositoryPort):
    def __init__(self, db_path: str = str(_DEFAULT_DB_PATH)) -> None:
        self._db_path = db_path
        self._migrate()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _migrate(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    name  TEXT    NOT NULL,
                    price REAL    NOT NULL
                )
                """
            )
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                conn.execute(
                    "INSERT INTO products (name, price) VALUES (?, ?)",
                    ("Coffee Mug", 12.99),
                )
                conn.execute(
                    "INSERT INTO products (name, price) VALUES (?, ?)",
                    ("Laptop Stand", 45.00),
                )

    @staticmethod
    def _row_to_product(row: sqlite3.Row) -> Product:
        return Product(id=str(row["id"]), name=row["name"], price=row["price"])

    async def get_all(self) -> list[Product]:
        def _query():
            with self._connection() as conn:
                rows = conn.execute("SELECT * FROM products").fetchall()
                return [self._row_to_product(r) for r in rows]

        return await asyncio.to_thread(_query)

    async def get_by_id(self, id: str) -> Optional[Product]:
        def _query():
            with self._connection() as conn:
                row = conn.execute(
                    "SELECT * FROM products WHERE id = ?", (id,)
                ).fetchone()
                return self._row_to_product(row) if row else None

        return await asyncio.to_thread(_query)

    async def create(self, name: str, price: float) -> Product:
        def _query():
            with self._connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO products (name, price) VALUES (?, ?)", (name, price)
                )
                return Product(id=str(cursor.lastrowid), name=name, price=price)

        return await asyncio.to_thread(_query)

    async def update(self, id: str, name: str, price: float) -> Optional[Product]:
        def _query():
            with self._connection() as conn:
                cursor = conn.execute(
                    "UPDATE products SET name = ?, price = ? WHERE id = ?",
                    (name, price, id),
                )
                if cursor.rowcount == 0:
                    return None
                return Product(id=str(id), name=name, price=price)

        return await asyncio.to_thread(_query)

    async def delete(self, id: str) -> bool:
        def _query():
            with self._connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM products WHERE id = ?", (id,)
                )
                return cursor.rowcount > 0

        return await asyncio.to_thread(_query)
