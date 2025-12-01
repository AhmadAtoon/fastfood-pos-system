from typing import List, Dict, Any
from models.order import Order
from models.payment import Payment

class TaxReports:
    def __init__(self, orders: List[Order], payments: List[Payment]):
        self.orders = orders
        self.payments = payments

    def generate_tax_summary(self) -> Dict[str, Any]:
        completed = [p for p in self.payments if p.status == "Completed"]
        gross_revenue = round(sum(p.amount for p in completed), 2)

        total_discount = 0.0
        for o in self.orders:
            da = getattr(o, "discount_amount", 0.0)
            total_discount += (da or 0.0)

        net_revenue = round(gross_revenue - total_discount, 2)

        return {
            "gross_revenue": gross_revenue,
            "total_discount": round(total_discount, 2),
            "net_revenue": net_revenue
        }

    def calculate_tax(self, rate: float = 0.09) -> float:
        summary = self.generate_tax_summary()
        return round(summary["net_revenue"] * rate, 2)

    def render_text_report(self, rate: float = 0.09) -> str:
        summary = self.generate_tax_summary()
        tax = self.calculate_tax(rate)
        lines = []
        lines.append(f"Tax Report | Gross Revenue: {summary['gross_revenue']} | Discounts: {summary['total_discount']} | Net Revenue: {summary['net_revenue']}")
        lines.append(f"Tax Rate: {rate*100}% | Tax Payable: {tax}")
        return "\n".join(lines)
