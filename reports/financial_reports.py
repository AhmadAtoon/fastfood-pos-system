from typing import List, Dict, Any
from models.order import Order
from models.payment import Payment

class FinancialReports:
    def __init__(self, orders: List[Order], payments: List[Payment]):
        self.orders = orders
        self.payments = payments

    def generate_financial_summary(self) -> Dict[str, Any]:
        completed = [p for p in self.payments if p.status == "Completed"]
        total_revenue = round(sum(p.amount for p in completed), 2)
        avg_payment = round(total_revenue / len(completed), 2) if completed else 0.0
        return {
            "total_orders": len(self.orders),
            "completed_payments": len(completed),
            "total_revenue": total_revenue,
            "average_payment": avg_payment
        }

    def discount_summary(self) -> Dict[str, Any]:
        total_discount = 0.0
        count = 0
        for o in self.orders:
            da = getattr(o, "discount_amount", 0.0)
            if da:
                total_discount += da
                count += 1
        avg_discount = round(total_discount / count, 2) if count > 0 else 0.0
        return {
            "total_discount": round(total_discount, 2),
            "average_discount": avg_discount,
            "discounted_orders": count
        }

    def net_revenue(self) -> float:
        summary = self.generate_financial_summary()
        discounts = self.discount_summary()
        return round(summary["total_revenue"] - discounts["total_discount"], 2)

    def render_text_report(self) -> str:
        summary = self.generate_financial_summary()
        discounts = self.discount_summary()
        net = self.net_revenue()
        lines = []
        lines.append(f"Financial Report | Orders: {summary['total_orders']} | Completed Payments: {summary['completed_payments']}")
        lines.append(f"Revenue: {summary['total_revenue']} | Avg Payment: {summary['average_payment']}")
        lines.append(f"Discounts: {discounts['total_discount']} | Avg Discount: {discounts['average_discount']} | Discounted Orders: {discounts['discounted_orders']}")
        lines.append(f"Net Revenue: {net}")
        return "\n".join(lines)
