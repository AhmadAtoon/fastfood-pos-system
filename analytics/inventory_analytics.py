from typing import Dict, Any, List
from collections import defaultdict
from models.inventory import Inventory
from models.order import Order

class InventoryAnalytics:
    def __init__(self, inventory: Inventory, orders: List[Order]):
        self.inventory = inventory
        self.orders = orders

    def inventory_value_by_category(self) -> Dict[str, float]:
        report = defaultdict(float)
        for pid, info in self.inventory.products.items():
            cat = info["product"].category
            report[cat] += info["product"].price * info["quantity"]
        return dict(report)

    def fast_moving_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        counts = defaultdict(int)
        for o in self.orders:
            for item in o.products:
                p = item["product"]
                q = item["quantity"]
                counts[p.name] += q
        ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"name": name, "qty": qty} for name, qty in ranked[:limit]]

    def slow_moving_products(self, threshold: int = 2) -> List[Dict[str, Any]]:
        result = []
        for pid, info in self.inventory.products.items():
            if info["quantity"] <= threshold:
                result.append({"name": info["product"].name, "stock": info["quantity"]})
        return result

    def average_stock(self) -> float:
        if not self.inventory.products:
            return 0.0
        total_qty = sum(info["quantity"] for info in self.inventory.products.values())
        return round(total_qty / len(self.inventory.products), 2)

    def render_text_analysis(self) -> str:
        cats = self.inventory_value_by_category()
        fast = self.fast_moving_products(limit=5)
        slow = self.slow_moving_products(threshold=2)
        avg = self.average_stock()
        lines = []
        lines.append("Inventory Analytics Report")
        lines.append("=" * 40)
        lines.append("Inventory Value by Category:")
        for cat, val in cats.items():
            lines.append(f" - {cat}: {val}")
        lines.append(f"Average Stock per Product: {avg}")
        lines.append("-" * 40)
        lines.append("Fast Moving Products:")
        for f in fast:
            lines.append(f" - {f['name']}: {f['qty']} sold")
        lines.append("-" * 40)
        lines.append("Slow Moving Products:")
        for s in slow:
            lines.append(f" - {s['name']}: {s['stock']} in stock")
        return "\n".join(lines)
