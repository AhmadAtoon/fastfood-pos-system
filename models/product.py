from datetime import datetime
from typing import Optional

class Product:
    def __init__(
        self,
        product_id: int,
        name: str,
        price: float,
        category: str,
        stock: int = 0,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.category = category
        self.stock = stock
        self.description = description
        self.created_at = created_at or datetime.now()

    def update_stock(self, amount: int) -> None:
        self.stock += amount
        if self.stock < 0:
            self.stock = 0

    def apply_discount(self, percent: float) -> None:
        if percent < 0 or percent > 100:
            raise ValueError("Discount percent must be between 0 and 100")
        self.price = round(self.price * (1 - percent / 100), 2)

    def update_price(self, new_price: float) -> None:
        if new_price <= 0:
            raise ValueError("Price must be positive")
        self.price = round(new_price, 2)

    def update_name(self, new_name: str) -> None:
        if not new_name:
            raise ValueError("Name cannot be empty")
        self.name = new_name.strip()

    def update_category(self, new_category: str) -> None:
        if not new_category:
            raise ValueError("Category cannot be empty")
        self.category = new_category.strip()

    def update_description(self, new_description: Optional[str]) -> None:
        self.description = new_description.strip() if new_description else None

    def edit_product(self, name=None, price=None, category=None, description=None) -> None:
        if name is not None:
            self.update_name(name)
        if price is not None:
            self.update_price(price)
        if category is not None:
            self.update_category(category)
        if description is not None:
            self.update_description(description)

    def is_available(self) -> bool:
        return self.stock > 0

    def __repr__(self) -> str:
        return f"<Product id={self.product_id} name={self.name} price={self.price} stock={self.stock}>"
