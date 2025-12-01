from typing import List, Dict, Any
from collections import defaultdict
from models.customer import Customer
from models.order import Order
from models.payment import Payment

class CustomerAnalytics:
    def __init__(self, customers: List[Customer], orders: List[Order], payments: List[Payment]):
        self.customers = customers
        self.orders = orders
        self.payments = payments

    def customer_lifetime_value(self) -> Dict[str, float]:
        """
        مجموع پرداخت‌های تکمیل‌شده هر مشتری (CLV ساده)
        """
        values = defaultdict(float)
        for p in self.payments:
            if getattr(p, "status", None) == "Completed":
                cust_name = getattr(getattr(p, "order", None), "customer", None)
                cust_name = getattr(cust_name, "name", None)
                if cust_name:
                    values[cust_name] += float(getattr(p, "amount", 0.0))
        return dict(values)

    def loyal_customers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        مشتریان وفادار بر اساس تعداد سفارش
        """
        counts = defaultdict(int)
        for o in self.orders:
            cust_name = getattr(getattr(o, "customer", None), "name", None)
            if cust_name:
                counts[cust_name] += 1
        ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"name": name, "orders": orders} for name, orders in ranked[:limit]]

    def average_purchase_per_customer(self) -> float:
        """
        میانگین مبلغ خرید هر مشتری فعال
        """
        values = self.customer_lifetime_value()
        if not values:
            return 0.0
        return round(sum(values.values()) / len(values), 2)

    def customer_distribution(self) -> Dict[str, int]:
        """
        توزیع مشتریان بر اساس آدرس (شهر)
        """
        dist = defaultdict(int)
        for c in self.customers:
            city = getattr(c, "address", "Unknown")
            dist[city] += 1
        return dict(dist)

    def render_text_analysis(self) -> str:
        """
        خروجی متنی تحلیل مشتری
        """
        values = self.customer_lifetime_value()
        loyal = self.loyal_customers(limit=5)
        avg = self.average_purchase_per_customer()
        dist = self.customer_distribution()
        lines = []
        lines.append("Customer Analytics Report")
        lines.append("=" * 40)
        lines.append("Customer Lifetime Value:")
        for name, val in values.items():
            lines.append(f" - {name}: {val}")
        lines.append(f"Average Purchase per Customer: {avg}")
        lines.append("-" * 40)
        lines.append("Loyal Customers:")
        for lc in loyal:
            lines.append(f" - {lc['name']}: {lc['orders']} orders")
        lines.append("-" * 40)
        lines.append("Customer Distribution:")
        for cat, count in dist.items():
            lines.append(f" - {cat}: {count} customers")
        return "\n".join(lines)
