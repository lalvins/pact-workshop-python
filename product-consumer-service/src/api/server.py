import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from adapters.product_service_http_adapter import ProductServiceHttpAdapter
from application.get_product_use_case import GetProductUseCase
from domain.product_not_found_error import ProductNotFoundError

app = FastAPI()

_provider_url = os.environ.get("PROVIDER_URL", "http://localhost:3001")
_adapter = ProductServiceHttpAdapter(_provider_url)
_get_product_use_case = GetProductUseCase(_adapter)


@app.get("/product/{product_id}")
async def get_product(product_id: str):
    try:
        product = await _get_product_use_case.execute(product_id)
        return {"id": product.id, "name": product.name, "price": product.price}
    except ProductNotFoundError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})


if __name__ == "__main__":
    print(f"Product Consumer running on http://localhost:3000")
    print(f"  → Calling provider at {_provider_url}")
    uvicorn.run(app, host="0.0.0.0", port=3000)
