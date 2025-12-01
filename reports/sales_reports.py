from datetime import datetime
from typing import List, Dict, Any, Optional

# این کلاس‌ها فرض شده‌اند در models موجودند و توسط سیستم شما استفاده می‌شوند.
from models.order import Order
from models.payment import Payment
from models.discount import Discount

class SalesReports:
    def __init__(self, orders: List[Order], payments: List[Payment], discounts: Optional[List[Discount]] = None):
        self.orders = orders
        self.payments = payments
        self.discounts = discounts or []

    def generate_sales_summary(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> Dict[str, Any]:
        """
        خلاصه فروش: تعداد سفارش، تعداد پرداخت تکمیل‌شده، مجموع دریافتی (فقط پرداخت‌های Completed)،
        میانگین مبلغ پرداخت، مجموع تخفیف اعمال‌شده (در صورت وجود داده).
        """
        filtered_orders = [o for o in self.orders if self._in_range(getattr(o, "created_at", None), start, end)]
        filtered_payments = [p for p in self.payments if self._in_range(p.paid_at, start, end) and p.status == "Completed"]

        total_orders = len(filtered_orders)
        completed_payments = len(filtered_payments)
        total_revenue = round(sum(p.amount for p in filtered_payments), 2)
        avg_payment = round(total_revenue / completed_payments, 2) if completed_payments > 0 else 0.0

        # اگر Order ها مقدار discount_amount دارند از آن استفاده می‌کنیم؛ در غیر این صورت صفر
        total_discount = 0.0
        for o in filtered_orders:
            da = getattr(o, "discount_amount", 0.0)
            total_discount += (da or 0.0)
        total_discount = round(total_discount, 2)

        return {
            "date_range": self._fmt_range(start, end),
            "total_orders": total_orders,
            "completed_payments": completed_payments,
            "total_revenue": total_revenue,
            "average_payment": avg_payment,
            "total_discount": total_discount
        }

    def top_products(self, limit: int = 5, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        محصولات پرفروش بر اساس تعداد، در بازه زمانی.
        """
        counts: Dict[int, Dict[str, Any]] = {}
        for o in self.orders:
            if not self._in_range(getattr(o, "created_at", None), start, end):
                continue
            for item in o.products:
                p = item["product"]
                q = item["quantity"]
                if p.product_id not in counts:
                    counts[p.product_id] = {"product_id": p.product_id, "name": p.name, "category": getattr(p, "category", None), "qty": 0, "revenue": 0.0}
                counts[p.product_id]["qty"] += q
                counts[p.product_id]["revenue"] += round(p.price * q, 2)

        ranked = sorted(counts.values(), key=lambda x: (x["qty"], x["revenue"]), reverse=True)
        return ranked[:limit]

    def top_customers(self, limit: int = 5, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        مشتریان برتر بر اساس مجموع پرداخت تکمیل‌شده در بازه زمانی.
        """
        # نگاشت order_id -> customer
        order_customer = {o.order_id: o.customer for o in self.orders}

        totals: Dict[int, Dict[str, Any]] = {}
        for p in self.payments:
            if p.status != "Completed" or not self._in_range(p.paid_at, start, end):
                continue
            cust = order_customer.get(p.order.order_id)
            if not cust:
                continue
            cid = cust.customer_id
            if cid not in totals:
                totals[cid] = {"customer_id": cid, "name": cust.name, "orders": 0, "revenue": 0.0}
            totals[cid]["orders"] += 1
            totals[cid]["revenue"] += round(p.amount, 2)

        ranked = sorted(totals.values(), key=lambda x: (x["revenue"], x["orders"]), reverse=True)
        return ranked[:limit]

    def render_text_report(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> str:
        """
        خروجی متنی استاندارد برای نمایش سریع در UI.
        """
        summary = self.generate_sales_summary(start, end)
        lines = []
        lines.append(f"Sales Report | Range: {summary['date_range']}")
        lines.append(f"Orders: {summary['total_orders']} | Completed Payments: {summary['completed_payments']}")
        lines.append(f"Revenue: {summary['total_revenue']} | Average Payment: {summary['average_payment']} | Discounts: {summary['total_discount']}")
        lines.append("-" * 40)
        lines.append("Top Products:")
        for tp in self.top_products(limit=5, start=start, end=end):
            lines.append(f" - {tp['name']} x{tp['qty']} | Rev: {round(tp['revenue'], 2)} | Cat: {tp['category']}")
        lines.append("-" * 40)
        lines.append("Top Customers:")
        for tc in self.top_customers(limit=5, start=start, end=end):
            lines.append(f" - {tc['name']} | Orders: {tc['orders']} | Rev: {round(tc['revenue'], 2)}")
        return "\n".join(lines)

    @staticmethod
    def _in_range(dt: Optional[datetime], start: Optional[datetime], end: Optional[datetime]) -> bool:
        if dt is None:
            return True if (start is None and end is None) else False
        if start and dt < start:
            return False
        if end and dt > end:
            return False
        return True

    @staticmethod
    def _fmt_range(start: Optional[datetime], end: Optional[datetime]) -> str:
        s = start.isoformat(timespec="seconds") if start else "-"
        e = end.isoformat(timespec="seconds") if end else "-"
        return f"{s} → {e}"
