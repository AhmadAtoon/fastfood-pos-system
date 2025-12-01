from datetime import datetime
from typing import List, Dict, Optional
from models.customer import Customer
from models.product import Product

class Order:
    def __init__(
        self,
        order_id: int,
        customer: Customer,
        products: Optional[List[Dict]] = None,
        status: str = "Pending",
        delivery_method: Optional[str] = None,
        delivery_fee: float = 0.0,
        created_at: Optional[datetime] = None
    ):
        self.order_id = order_id
        self.customer = customer
        self.products = products or []  # [{ "product": Product, "quantity": int }]
        self.status = status
        self.delivery_method = delivery_method
        self.delivery_fee = delivery_fee
        self.created_at = created_at or datetime.now()
        self.updated_at = self.created_at

    # --- مدیریت محصولات ---
    def add_product(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.products.append({"product": product, "quantity": quantity})
        self.updated_at = datetime.now()

    def remove_product(self, product_id: int) -> None:
        self.products = [p for p in self.products if p["product"].product_id != product_id]
        self.updated_at = datetime.now()

    def update_quantity(self, product_id: int, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        for p in self.products:
            if p["product"].product_id == product_id:
                p["quantity"] = quantity
                self.updated_at = datetime.now()
                return
        raise ValueError("Product not found in order")

    # --- محاسبات مالی ---
    def calculate_total(self) -> float:
        total = sum(p["product"].price * p["quantity"] for p in self.products)
        return round(total + self.delivery_fee, 2)

    def apply_discount(self, percent: float) -> None:
        if percent < 0 or percent > 100:
            raise ValueError("Discount percent must be between 0 and 100")
        for p in self.products:
            p["product"].price = round(p["product"].price * (1 - percent / 100), 2)
        self.updated_at = datetime.now()

    # --- مدیریت وضعیت ---
    def update_status(self, new_status: str) -> None:
        valid_statuses = ["Pending", "Paid", "Shipped", "Delivered", "Cancelled"]
        if new_status not in valid_statuses:
            raise ValueError("Invalid status")
        self.status = new_status
        self.updated_at = datetime.now()

    def is_completed(self) -> bool:
        return self.status == "Delivered"

    # --- ارسال ---
    def set_delivery(self, method: str, fee: float = 0.0) -> None:
        if not method:
            raise ValueError("Delivery method cannot be empty")
        self.delivery_method = method
        self.delivery_fee = fee
        self.updated_at = datetime.now()

    def get_delivery_info(self) -> str:
        return f"Method: {self.delivery_method}, Fee: {self.delivery_fee}, Address: {self.customer.address}"

    # --- نمایش ---
    def __repr__(self) -> str:
        return f"<Order id={self.order_id} customer={self.customer.name} status={self.status} total={self.calculate_total()}>"
