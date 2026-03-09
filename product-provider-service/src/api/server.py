from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from adapters.sqlite_product_repository import SQLiteProductRepository
from api.dependencies import get_repository
from ports.product_repository_port import ProductRepositoryPort


class ProductInput(BaseModel):
    name: str
    price: float


def create_app() -> FastAPI:
    """
    FastAPI app factory.

    Routes receive the repository via Depends(get_repository).
    Override the dependency after calling this function to swap the
    implementation, e.g. for Pact verification:

        app = create_app()
        app.dependency_overrides[get_repository] = lambda: InMemoryProductRepository()
    """
    app = FastAPI()

    @app.get("/products")
    async def get_all(
        repository: Annotated[ProductRepositoryPort, Depends(get_repository)],
    ):
        products = await repository.get_all()
        return [{"id": p.id, "name": p.name, "price": p.price} for p in products]

    @app.get("/products/{product_id}")
    async def get_by_id(
        product_id: str,
        repository: Annotated[ProductRepositoryPort, Depends(get_repository)],
    ):
        product = await repository.get_by_id(product_id)
        if product is None:
            return JSONResponse(status_code=404, content={"error": "Product not found"})
        return {"id": product.id, "name": product.name, "price": product.price}

    @app.post("/products", status_code=201)
    async def create_product(
        body: ProductInput,
        repository: Annotated[ProductRepositoryPort, Depends(get_repository)],
    ):
        product = await repository.create(name=body.name, price=body.price)
        return {"id": product.id, "name": product.name, "price": product.price}

    @app.put("/products/{product_id}")
    async def update_product(
        product_id: str,
        body: ProductInput,
        repository: Annotated[ProductRepositoryPort, Depends(get_repository)],
    ):
        product = await repository.update(id=product_id, name=body.name, price=body.price)
        if product is None:
            return JSONResponse(status_code=404, content={"error": "Product not found"})
        return {"id": product.id, "name": product.name, "price": product.price}

    @app.delete("/products/{product_id}")
    async def delete_product(
        product_id: str,
        repository: Annotated[ProductRepositoryPort, Depends(get_repository)],
    ):
        deleted = await repository.delete(product_id)
        if not deleted:
            return JSONResponse(status_code=404, content={"error": "Product not found"})
        return Response(status_code=204)

    return app


if __name__ == "__main__":
    print("Product Provider running on http://localhost:3001 [SQLite]")
    uvicorn.run(create_app(), host="0.0.0.0", port=3001)
