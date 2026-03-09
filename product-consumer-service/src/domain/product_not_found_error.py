class ProductNotFoundError(Exception):
    def __init__(self, product_id: str) -> None:
        super().__init__(f'Product with id "{product_id}" not found')
        self.product_id = product_id
