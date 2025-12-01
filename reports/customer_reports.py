from typing import List, Dict, Any
from models.customer import Customer
from models.order import Order
from models.payment import Payment

class CustomerReports:
    def __init__(self, customers: List[Customer], orders: List[Order], payments: List[Payment]):
        self.customers = customers
        self.orders = orders
        self.payments = payments

    def generate_customer_summary(self) -> Dict[str, Any]:
        active_customers = {o.customer.customer_id for o in self.orders}
        total_customers = len(self.customers)
        active_count = len(active_customers)
        avg_purchase = round(sum(p.amount for p in self.payments if p.status == "Completed") / active_count, 2) if active_count > 0 else 0.0
        return {
            "total_customers": total_customers,
            "active_customers": active_count,
            "average_purchase_per_active": avg_purchase
        }

    def top_customers(self, limit: int = 5) -> List[Dict[str, Any]]:
        totals: Dict[int, Dict[str, Any]] = {}
        for p in self.payments:
            if p.status != "Completed":
                continue
            cust = p.order.customer
            cid = cust.customer_id
            if cid not in totals:
                totals[cid] = {"customer_id": cid, "name": cust.name, "orders": 0, "revenue": 0.0}
            totals[cid]["orders"] += 1
            totals[cid]["revenue"] += round(p.amount, 2)
        ranked = sorted(totals.values(), key=lambda x: (x["revenue"], x["orders"]), reverse=True)
        return ranked[:limit]

    def loyal_customers(self, limit: int = 5) -> List[Dict[str, Any]]:
        counts: Dict[int, Dict[str, Any]] = {}
        for o in self.orders:
            cust = o.customer
            cid = cust.customer_id
            if cid not in counts:
                counts[cid] = {"customer_id": cid, "name": cust.name, "orders": 0}
            counts[cid]["orders"] += 1
        ranked = sorted(counts.values(), key=lambda x: x["orders"], reverse=True)
        return ranked[:limit]

    def customer_category_report(self) -> Dict[str, int]:
        report: Dict[str, int] = {}
        for c in self.customers:
            cat = getattr(c, "address", "Unknown")
            report[cat] = report.get(cat, 0) + 1
        return report

    def render_text_report(self) -> str:
        summary = self.generate_customer_summary()
        lines = []
        lines.append(f"Customer Report | Total: {summary['total_customers']} | Active: {summary['active_customers']} | Avg Purchase: {summary['average_purchase_per_active']}")
        lines.append("-" * 40)
        lines.append("Top Customers:")
        for tc in self.top_customers(limit=5):
            lines.append(f" - {tc['name']} | Orders: {tc['orders']} | Revenue: {tc['revenue']}")
        lines.append("-" * 40)
        lines.append("Loyal Customers:")
        for lc in self.loyal_customers(limit=5):
            lines.append(f" - {lc['name']} | Orders: {lc['orders']}")
        lines.append("-" * 40)
        lines.append("Customer Category Report:")
        for cat, count in self.customer_category_report().items():
            lines.append(f" - {cat}: {count} customers")
        return "\n".join(lines)
