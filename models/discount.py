from datetime import datetime
from typing import Optional, List, Dict
from models.order import Order

class Discount:
    def __init__(
        self,
        code: str,
        kind: str,  # "percentage" or "fixed"
        value: float,  # percent (0-100) or fixed amount
        scope: str = "order",  # "order", "category", "product"
        category: Optional[str] = None,
        product_id: Optional[int] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        min_order_total: float = 0.0,
        requires_membership: bool = False,
        usage_limit: Optional[int] = None
    ):
        self.code = code
        self.kind = kind
        self.value = value
        self.scope = scope
        self.category = category
        self.product_id = product_id
        self.start_at = start_at
        self.end_at = end_at
        self.min_order_total = min_order_total
        self.requires_membership = requires_membership
        self.usage_limit = usage_limit
        self.used_count = 0

    def is_valid(self, order: Order) -> bool:
        now = datetime.now()
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        if self.requires_membership and not order.customer.has_membership():
            return False
        if order.calculate_total() < self.min_order_total:
            return False
        return True

    def _eligible_line_totals(self, order: Order) -> float:
        total = 0.0
        for item in order.products:
            p = item["product"]
            q = item["quantity"]
            if self.scope == "order":
                total += p.price * q
            elif self.scope == "category" and self.category and p.category == self.category:
                total += p.price * q
            elif self.scope == "product" and self.product_id and p.product_id == self.product_id:
                total += p.price * q
        return total

    def calculate_discount(self, order: Order) -> float:
        if not self.is_valid(order):
            return 0.0
        base = self._eligible_line_totals(order)
        if self.kind == "percentage":
            if self.value < 0 or self.value > 100:
                return 0.0
            return round(base * (self.value / 100.0), 2)
        elif self.kind == "fixed":
            return round(min(self.value, base), 2)
        else:
            return 0.0

    def apply_to_order(self, order: Order) -> (float, float):
        """
        Returns (discount_amount, new_order_total).
        Does not mutate order prices. Delivery fee is included in new total.
        """
        discount_amount = self.calculate_discount(order)
        new_total = max(0.0, round(order.calculate_total() - discount_amount, 2))
        return discount_amount, new_total

    def consume(self) -> None:
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            raise ValueError("Usage limit reached")
        self.used_count += 1

    def __repr__(self) -> str:
        return f"<Discount code={self.code} kind={self.kind} value={self.value} scope={self.scope} used={self.used_count}>"
