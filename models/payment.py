from datetime import datetime
from typing import Optional
from models.order import Order

class Payment:
    def __init__(
        self,
        payment_id: int,
        order: Order,
        amount: float,
        method: str,
        status: str = "Pending",
        transaction_code: Optional[str] = None,
        paid_at: Optional[datetime] = None
    ):
        self.payment_id = payment_id
        self.order = order
        self.amount = amount
        self.method = method
        self.status = status
        self.transaction_code = transaction_code
        self.paid_at = paid_at

    # --- مدیریت وضعیت پرداخت ---
    def process_payment(self, success: bool, transaction_code: Optional[str] = None) -> None:
        """
        در نسخه اصلاح‌شده، مبلغ پرداخت را تنها از نظر مثبت بودن بررسی می‌کنیم.
        تفاوت با مجموع سفارش قابل قبول است (به‌دلیل تخفیف‌ها/کوپن‌ها/خطای گرد کردن).
        """
        if success:
            if self.amount <= 0:
                raise ValueError("Payment amount must be positive")
            self.status = "Completed"
            self.transaction_code = transaction_code or f"TX-{self.payment_id}-{int(datetime.now().timestamp())}"
            self.paid_at = datetime.now()
        else:
            self.status = "Failed"

    def refund(self) -> None:
        if self.status != "Completed":
            raise ValueError("Only completed payments can be refunded")
        self.status = "Refunded"

    def update_status(self, new_status: str) -> None:
        valid_statuses = ["Pending", "Completed", "Failed", "Refunded"]
        if new_status not in valid_statuses:
            raise ValueError("Invalid payment status")
        self.status = new_status

    # --- اطلاعات پرداخت ---
    def get_payment_info(self) -> str:
        return f"Payment ID: {self.payment_id}, Method: {self.method}, Status: {self.status}, Amount: {self.amount}, Transaction: {self.transaction_code or '-'}"

    # --- پیش‌نمایش فاکتور ---
    def generate_invoice_preview(self) -> str:
        lines = []
        lines.append(f"--- Invoice Preview ---")
        lines.append(f"Order ID: {self.order.order_id}")
        lines.append(f"Customer: {self.order.customer.name}")
        lines.append(f"Address: {self.order.customer.address}")
        lines.append(f"Payment Method: {self.method}")
        lines.append(f"Status: {self.status}")
        lines.append(f"Transaction Code: {self.transaction_code or '-'}")
        lines.append("Products:")
        for item in self.order.products:
            p = item["product"]
            q = item["quantity"]
            lines.append(f" - {p.name} x{q} = {round(p.price * q, 2)}")
        lines.append(f"Delivery: {self.order.delivery_method} ({self.order.delivery_fee})")
        lines.append(f"Order Total: {self.order.calculate_total()}")
        lines.append(f"Paid Amount: {self.amount}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<Payment id={self.payment_id} order={self.order.order_id} status={self.status} amount={self.amount}>"
