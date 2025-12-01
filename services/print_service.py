from typing import Dict, Any, List, Optional
from datetime import datetime
from fpdf import FPDF
from services.auth_service import AuthService

class PrintService:
    """
    سرویس چاپ PDF با پشتیبانی از template_config ساده و چک مجوزها.
    اگر نمونهٔ AuthService به سازنده پاس داده شود، متدهای چاپ قبل از اجرا
    بررسی مجوز خواهند شد. پارامتر actor_token در متدها اختیاری است.
    """

    def __init__(self, auth_service: Optional[AuthService] = None):
        self.auth = auth_service

    def _format_money(self, amount: float) -> str:
        return f"{int(round(amount)):,}"

    def _epoch_to_str(self, ts: int) -> str:
        try:
            return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "-"

    def _check_permission(self, token: Optional[str], permission: str):
        """
        اگر auth service موجود باشد، بررسی می‌کند که token دارای permission است.
        در صورت عدم وجود token یا عدم مجوز، PermissionError پرتاب می‌شود.
        اگر auth service وجود نداشته باشد، چک نادیده گرفته می‌شود.
        """
        if not self.auth:
            return
        if not token:
            raise PermissionError("Missing actor token for permission check")
        # اجازه اگر print.any یا permission خاص وجود داشته باشد
        if self.auth.has_permission(token, "print.any"):
            return
        if not self.auth.has_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission}")

    def _apply_margins_and_font(self, pdf: FPDF, template_config: Optional[Dict[str, Any]]):
        margins = (template_config or {}).get("margins", {})
        left = margins.get("left", 10)
        top = margins.get("top", 10)
        right = margins.get("right", 10)
        pdf.set_left_margin(left)
        pdf.set_top_margin(top)
        pdf.set_right_margin(right)
        font_cfg = (template_config or {}).get("font", {})
        font_name = font_cfg.get("name", "Arial")
        font_size = font_cfg.get("size", 11)
        pdf.set_font(font_name, size=font_size)

    def _render_header(self, pdf: FPDF, header_cfg: Dict[str, Any]):
        lines = header_cfg.get("lines", [])
        align = header_cfg.get("align", "C")
        pdf.set_font("", "B")
        for line in lines:
            pdf.cell(0, 8, str(line), ln=True, align=align)
        pdf.ln(2)
        pdf.set_font("", "")

    def _render_footer(self, pdf: FPDF, footer_cfg: Dict[str, Any]):
        lines = footer_cfg.get("lines", [])
        align = footer_cfg.get("align", "C")
        pdf.ln(4)
        pdf.set_font("", "")
        for line in lines:
            pdf.cell(0, 6, str(line), ln=True, align=align)

    def _render_table_header(self, pdf: FPDF, columns: List[Dict[str, Any]]):
        pdf.set_font("", "B")
        for col in columns:
            title = col.get("title", col.get("key", ""))
            w = float(col.get("width", 40))
            align = col.get("align", "L")
            pdf.cell(w, 8, str(title), 1, 0, align)
        pdf.ln()
        pdf.set_font("", "")

    def _render_table_lines(self, pdf: FPDF, columns: List[Dict[str, Any]], lines: List[Dict[str, Any]]):
        for ln in lines:
            for col in columns:
                key = col.get("key")
                w = float(col.get("width", 40))
                align = col.get("align", "L")
                val = ln.get(key, "")
                if isinstance(val, (int, float)):
                    text = self._format_money(float(val))
                else:
                    text = str(val)
                pdf.cell(w, 8, text, 1, 0, align)
            pdf.ln()

    def print_invoice(self, invoice_data: Dict[str, Any], filename: str, template_config: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> str:
        """
        تولید فاکتور رسمی PDF.
        نیاز به مجوز 'print.invoice' یا 'print.any' در صورت وجود AuthService.
        """
        # بررسی مجوز
        self._check_permission(actor_token, "print.invoice")

        header = invoice_data.get("header", {})
        lines: List[Dict[str, Any]] = invoice_data.get("lines", [])
        totals = invoice_data.get("totals", {})

        pdf = FPDF()
        pdf.add_page()
        self._apply_margins_and_font(pdf, template_config)

        if template_config and template_config.get("header"):
            self._render_header(pdf, template_config["header"])
        else:
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Invoice", ln=True, align="C")
            pdf.set_font("Arial", "", 11)

        pdf.cell(0, 8, f"Order ID: {header.get('order_id','-')}", ln=True)
        pdf.cell(0, 8, f"Customer ID: {header.get('customer_id','-')}", ln=True)
        pdf.cell(0, 8, f"Status: {header.get('status','-')}", ln=True)
        pdf.cell(0, 8, f"Date: {self._epoch_to_str(header.get('created_at', 0))}", ln=True)
        pdf.ln(2)

        table_cfg = (template_config or {}).get("table")
        if table_cfg and table_cfg.get("columns"):
            columns = table_cfg["columns"]
        else:
            columns = [
                {"key": "name", "title": "Item", "width": 80, "align": "L"},
                {"key": "qty", "title": "Qty", "width": 20, "align": "C"},
                {"key": "price", "title": "Price", "width": 30, "align": "R"},
                {"key": "discount", "title": "Discount", "width": 30, "align": "R"},
                {"key": "line_total", "title": "Line total", "width": 30, "align": "R"},
            ]

        self._render_table_header(pdf, columns)
        self._render_table_lines(pdf, columns, lines)

        pdf.ln(4)
        pdf.set_font("", "B")
        pdf.cell(0, 8, f"Subtotal: {self._format_money(float(totals.get('subtotal', 0)))}", ln=True, align="R")
        pdf.cell(0, 8, f"Discount: {self._format_money(float(totals.get('discount_total', 0)))}", ln=True, align="R")
        pdf.cell(0, 8, f"Tax: {self._format_money(float(totals.get('tax', 0)))}", ln=True, align="R")
        pdf.cell(0, 8, f"Grand total: {self._format_money(float(totals.get('grand_total', 0)))}", ln=True, align="R")

        if template_config and template_config.get("footer"):
            self._render_footer(pdf, template_config["footer"])

        pdf.output(filename)
        return filename

    def print_kitchen_ticket(self, order_like: Dict[str, Any], filename: str, template_config: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> str:
        """
        تولید تیکت آشپزخانه.
        نیاز به مجوز 'print.kitchen' یا 'print.any' در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "print.kitchen")

        pdf = FPDF()
        pdf.add_page()
        self._apply_margins_and_font(pdf, template_config)

        if template_config and template_config.get("header"):
            self._render_header(pdf, template_config["header"])
        else:
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Kitchen Ticket", ln=True, align="C")

        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Order: {order_like.get('order_id','-')}", ln=True)
        pdf.cell(0, 8, f"Time: {self._epoch_to_str(order_like.get('created_at', 0))}", ln=True)
        pdf.ln(2)

        columns = (template_config or {}).get("table", {}).get("columns") or [
            {"key": "name", "title": "Item", "width": 120, "align": "L"},
            {"key": "qty", "title": "Qty", "width": 30, "align": "C"},
        ]
        self._render_table_header(pdf, columns)
        self._render_table_lines(pdf, columns, order_like.get("items", []))

        if template_config and template_config.get("footer"):
            self._render_footer(pdf, template_config["footer"])

        pdf.output(filename)
        return filename

    def print_receipt(self, order_like: Dict[str, Any], filename: str, template_config: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> str:
        """
        تولید رسید مشتری.
        نیاز به مجوز 'print.receipt' یا 'print.any' در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "print.receipt")

        pdf = FPDF()
        pdf.add_page()
        self._apply_margins_and_font(pdf, template_config)

        if template_config and template_config.get("header"):
            self._render_header(pdf, template_config["header"])
        else:
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Receipt", ln=True, align="C")

        pdf.cell(0, 8, f"Order: {order_like.get('order_id','-')}", ln=True)
        pdf.cell(0, 8, f"Time: {self._epoch_to_str(order_like.get('created_at', 0))}", ln=True)
        pdf.ln(2)

        columns = (template_config or {}).get("table", {}).get("columns") or [
            {"key": "name", "title": "Item", "width": 110, "align": "L"},
            {"key": "qty", "title": "Qty", "width": 30, "align": "C"},
            {"key": "line_total", "title": "Amount", "width": 40, "align": "R"},
        ]
        self._render_table_header(pdf, columns)
        lines = order_like.get("lines") or [
            {"name": it.get("name"), "qty": it.get("qty"), "line_total": it.get("qty",0)*it.get("price",0)} for it in order_like.get("items", [])
        ]
        self._render_table_lines(pdf, columns, lines)

        totals = order_like.get("totals", {})
        pdf.ln(4)
        pdf.set_font("", "B")
        pdf.cell(0, 8, f"Subtotal: {self._format_money(float(totals.get('subtotal', 0)))}", ln=True, align="R")
        pdf.cell(0, 8, f"Discount: {self._format_money(float(totals.get('discount_total', 0)))}", ln=True, align="R")
        pdf.cell(0, 8, f"Tax: {self._format_money(float(totals.get('tax', 0)))}", ln=True, align="R")
        pdf.cell(0, 8, f"Grand total: {self._format_money(float(totals.get('grand_total', 0)))}", ln=True, align="R")

        if template_config and template_config.get("footer"):
            self._render_footer(pdf, template_config["footer"])

        pdf.output(filename)
        return filename
