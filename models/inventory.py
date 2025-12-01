from datetime import datetime
from typing import Dict, Optional
from models.product import Product

class Inventory:
    def __init__(self):
        # {product_id: {"product": Product, "quantity": int}}
        self.products: Dict[int, Dict] = {}
        self.last_updated: Optional[datetime] = None

    # --- مدیریت محصول ---
    def add_product(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if product.product_id in self.products:
            self.products[product.product_id]["quantity"] += quantity
        else:
            self.products[product.product_id] = {"product": product, "quantity": quantity}
        self.last_updated = datetime.now()

    def remove_product(self, product_id: int) -> None:
        if product_id in self.products:
            del self.products[product_id]
            self.last_updated = datetime.now()

    def update_stock(self, product_id: int, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if product_id not in self.products:
            raise ValueError("Product not found")
        self.products[product_id]["quantity"] = quantity
        self.last_updated = datetime.now()

    # --- جستجو و گزارش ---
    def get_product(self, product_id: int) -> Optional[Dict]:
        return self.products.get(product_id)

    def list_all_products(self) -> Dict[int, Dict]:
        return self.products

    def search_by_category(self, category: str) -> Dict[int, Dict]:
        return {pid: info for pid, info in self.products.items() if info["product"].category == category}

    # --- کنترل موجودی ---
    def check_availability(self, product_id: int, quantity: int) -> bool:
        if product_id not in self.products:
            return False
        return self.products[product_id]["quantity"] >= quantity

    def low_stock_alert(self, threshold: int) -> Dict[int, Dict]:
        return {pid: info for pid, info in self.products.items() if info["quantity"] < threshold}

    # --- محاسبات ---
    def calculate_inventory_value(self) -> float:
        return round(sum(info["product"].price * info["quantity"] for info in self.products.values()), 2)

    def generate_inventory_report(self) -> str:
        lines = ["--- Inventory Report ---"]
        for pid, info in self.products.items():
            p = info["product"]
            q = info["quantity"]
            lines.append(f"{p.name} (ID:{pid}) | Category: {p.category} | Price: {p.price} | Stock: {q}")
        lines.append(f"Total Inventory Value: {self.calculate_inventory_value()}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<Inventory items={len(self.products)} value={self.calculate_inventory_value()}>"
