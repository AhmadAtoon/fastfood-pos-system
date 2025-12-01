from datetime import datetime
from typing import Optional, Dict, Any, List
from models.order import Order
from models.payment import Payment

class Invoice:
    def __init__(
        self,
        invoice_id: int,
        order: Order,
        payment: Payment,
        discount_amount: float = 0.0,
        store_name: str = "My FastFood POS",
        store_address: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.invoice_id = invoice_id
        self.order = order
        self.payment = payment
        self.discount_amount = round(discount_amount, 2)
        self.store_name = store_name
        self.store_address = store_address or "Tehran, Iran"
        self.created_at = created_at or datetime.now()

    def generate_data(self) -> Dict[str, Any]:
        lines: List[Dict[str, Any]] = []
        subtotal = 0.0
        for item in self.order.products:
            p = item["product"]
            q = item["quantity"]
            line_total = round(p.price * q, 2)
            lines.append({
                "name": p.name,
                "quantity": q,
                "unit_price": p.price,
                "line_total": line_total,
                "category": getattr(p, "category", None)
            })
            subtotal += line_total

        delivery = round(self.order.delivery_fee, 2)
        discount = self.discount_amount
        total = round(subtotal + delivery - discount, 2)

        return {
            "invoice_id": self.invoice_id,
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "store": {"name": self.store_name, "address": self.store_address},
            "customer": {
                "id": self.order.customer.customer_id,
                "name": self.order.customer.name,
                "address": self.order.customer.address,
                "membership": self.order.customer.membership_code or "-"
            },
            "order": {"id": self.order.order_id, "status": self.order.status},
            "payment": {
                "id": self.payment.payment_id,
                "method": self.payment.method,
                "status": self.payment.status,
                "transaction_code": self.payment.transaction_code or "-",
                "paid_at": self.payment.paid_at.isoformat(timespec="seconds") if self.payment.paid_at else "-"
            },
            "lines": lines,
            "summary": {
                "subtotal": round(subtotal, 2),
                "delivery": delivery,
                "discount": discount,
                "total": total
            }
        }

    def render_text_preview(self) -> str:
        data = self.generate_data()
        lines = []
        lines.append(f"{data['store']['name']} - {data['store']['address']}")
        lines.append(f"Invoice #{data['invoice_id']} | Date: {data['created_at']}")
        lines.append(f"Order #{data['order']['id']} | Status: {data['order']['status']}")
        lines.append(f"Customer: {data['customer']['name']} | Addr: {data['customer']['address']} | Member: {data['customer']['membership']}")
        lines.append(f"Payment: {data['payment']['method']} | Status: {data['payment']['status']} | Tx: {data['payment']['transaction_code']}")
        lines.append("-" * 40)
        lines.append("Items:")
        for li in data["lines"]:
            lines.append(f" - {li['name']} x{li['quantity']} @ {li['unit_price']} = {li['line_total']}")
        lines.append("-" * 40)
        s = data["summary"]
        lines.append(f"Subtotal: {s['subtotal']}")
        lines.append(f"Delivery: {s['delivery']}")
        lines.append(f"Discount: {s['discount']}")
        lines.append(f"TOTAL: {s['total']}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return self.generate_data()

    def print_preview(self) -> str:
        # In real system, send to printer; here we just return the preview string.
        return self.render_text_preview()

    def __repr__(self) -> str:
        return f"<Invoice id={self.invoice_id} order={self.order.order_id} total={self.generate_data()['summary']['total']}>"
