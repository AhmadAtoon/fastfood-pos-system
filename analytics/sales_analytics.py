from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from models.order import Order

class SalesAnalytics:
    def __init__(self, orders: List[Order]):
        self.orders = orders

    def sales_trend(self, period: str = "daily") -> Dict[str, float]:
        """
        تحلیل روند فروش بر اساس بازه زمانی (daily, monthly)
        """
        trend = defaultdict(float)
        for o in self.orders:
            dt: datetime = getattr(o, "created_at", None)
            if not dt:
                continue
            if period == "daily":
                key = dt.strftime("%Y-%m-%d")
            elif period == "monthly":
                key = dt.strftime("%Y-%m")
            else:
                key = "unknown"
            trend[key] += o.calculate_total()
        return dict(trend)

    def average_sales(self, period: str = "daily") -> float:
        trend = self.sales_trend(period)
        if not trend:
            return 0.0
        return round(sum(trend.values()) / len(trend), 2)

    def top_products_over_time(self, period: str = "daily") -> Dict[str, Dict[str, int]]:
        """
        محصولات پرفروش در هر بازه زمانی
        """
        result: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for o in self.orders:
            dt: datetime = getattr(o, "created_at", None)
            if not dt:
                continue
            if period == "daily":
                key = dt.strftime("%Y-%m-%d")
            elif period == "monthly":
                key = dt.strftime("%Y-%m")
            else:
                key = "unknown"
            for item in o.products:
                p = item["product"]
                q = item["quantity"]
                result[key][p.name] += q
        return result

    def render_text_analysis(self, period: str = "daily") -> str:
        trend = self.sales_trend(period)
        avg = self.average_sales(period)
        top_products = self.top_products_over_time(period)
        lines = []
        lines.append(f"Sales Analytics Report ({period})")
        lines.append("=" * 40)
        lines.append("Sales Trend:")
        for k, v in trend.items():
            lines.append(f" - {k}: {v}")
        lines.append(f"Average Sales: {avg}")
        lines.append("-" * 40)
        lines.append("Top Products Over Time:")
        for k, products in top_products.items():
            lines.append(f"[{k}]")
            for pname, qty in products.items():
                lines.append(f" - {pname}: {qty}")
        return "\n".join(lines)
