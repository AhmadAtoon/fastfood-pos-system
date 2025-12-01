from typing import Dict, Any, List
from models.inventory import Inventory
from models.order import Order

class InventoryReports:
    def __init__(self, inventory: Inventory, orders: List[Order] = None):
        self.inventory = inventory
        self.orders = orders or []

    def generate_inventory_summary(self) -> Dict[str, Any]:
        """
        خلاصه موجودی: تعداد محصولات، ارزش کل موجودی، تاریخ آخرین بروزرسانی
        """
        return {
            "total_products": len(self.inventory.products),
            "total_value": self.inventory.calculate_inventory_value(),
            "last_updated": self.inventory.last_updated.isoformat() if self.inventory.last_updated else "-"
        }

    def low_stock_products(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """
        محصولات با موجودی کمتر از threshold
        """
        alerts = self.inventory.low_stock_alert(threshold)
        return [
            {
                "product_id": pid,
                "name": info["product"].name,
                "stock": info["quantity"],
                "category": info["product"].category
            }
            for pid, info in alerts.items()
        ]

    def category_stock_report(self) -> Dict[str, Dict[str, Any]]:
        """
        گزارش دسته‌بندی‌ها: مجموع موجودی و ارزش هر دسته
        """
        report: Dict[str, Dict[str, Any]] = {}
        for pid, info in self.inventory.products.items():
            cat = info["product"].category
            if cat not in report:
                report[cat] = {"total_qty": 0, "total_value": 0.0}
            report[cat]["total_qty"] += info["quantity"]
            report[cat]["total_value"] += round(info["product"].price * info["quantity"], 2)
        return report

    def top_consumed_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        محصولات پرفروش بر اساس سفارش‌ها (کاهش موجودی)
        """
        counts: Dict[int, Dict[str, Any]] = {}
        for o in self.orders:
            for item in o.products:
                p = item["product"]
                q = item["quantity"]
                if p.product_id not in counts:
                    counts[p.product_id] = {"product_id": p.product_id, "name": p.name, "qty": 0}
                counts[p.product_id]["qty"] += q
        ranked = sorted(counts.values(), key=lambda x: x["qty"], reverse=True)
        return ranked[:limit]

    def render_text_report(self) -> str:
        """
        خروجی متنی مدیریتی
        """
        summary = self.generate_inventory_summary()
        lines = []
        lines.append(f"Inventory Report | Products: {summary['total_products']} | Value: {summary['total_value']} | Last Updated: {summary['last_updated']}")
        lines.append("-" * 40)
        lines.append("Category Stock Report:")
        for cat, data in self.category_stock_report().items():
            lines.append(f" - {cat}: Qty={data['total_qty']} | Value={data['total_value']}")
        lines.append("-" * 40)
        lines.append("Low Stock Products:")
        for lp in self.low_stock_products(threshold=5):
            lines.append(f" - {lp['name']} | Stock={lp['stock']} | Cat={lp['category']}")
        lines.append("-" * 40)
        lines.append("Top Consumed Products:")
        for tp in self.top_consumed_products(limit=5):
            lines.append(f" - {tp['name']} | Ordered Qty={tp['qty']}")
        return "\n".join(lines)
