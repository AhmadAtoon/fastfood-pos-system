import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os

from services.print_service import PrintService

# نمونه دادهٔ استاندارد (همخوان با generate_invoice_data در OrderService)
ORDER_SAMPLE = {
    "order_id": "ORD-123",
    "customer_id": 1001,
    "status": "paid",
    "created_at": 1732886400,
    "items": [
        {"product_id": 1, "name": "Burger", "qty": 2, "price": 120000, "discount": {"percent": 10}},
        {"product_id": 2, "name": "Soda", "qty": 3, "price": 20000},
        {"product_id": 3, "name": "Fries", "qty": 1, "price": 50000, "discount": {"amount": 5000}},
    ],
    "totals": {
        "subtotal": 310000,
        "discount_total": 29000,
        "tax": 25290,
        "grand_total": 306290,
    }
}

INVOICE_SAMPLE = {
    "header": {
        "order_id": ORDER_SAMPLE["order_id"],
        "customer_id": ORDER_SAMPLE["customer_id"],
        "status": ORDER_SAMPLE["status"],
        "created_at": ORDER_SAMPLE["created_at"],
        "tax_rate": 9.0,
    },
    "lines": [
        {"name": "Burger", "qty": 2, "price": 120000, "discount": 24000, "line_total": 216000},
        {"name": "Soda", "qty": 3, "price": 20000, "discount": 0, "line_total": 60000},
        {"name": "Fries", "qty": 1, "price": 50000, "discount": 5000, "line_total": 45000},
    ],
    "totals": ORDER_SAMPLE["totals"],
}


class TestPrintService(unittest.TestCase):
    def setUp(self):
        self.srv = PrintService()

    def test_print_invoice_pdf(self):
        path = self.srv.print_invoice(INVOICE_SAMPLE, "out_invoice.pdf")
        self.assertTrue(os.path.exists(path))

    def test_print_kitchen_ticket_pdf(self):
        path = self.srv.print_kitchen_ticket(ORDER_SAMPLE, "out_kitchen.pdf")
        self.assertTrue(os.path.exists(path))

    def test_print_receipt_pdf(self):
        path = self.srv.print_receipt(ORDER_SAMPLE, "out_receipt.pdf")
        self.assertTrue(os.path.exists(path))


def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPrintService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestPrintService)
    status_map = {name: ("✅ Passed", "") for name in expected}
    for test, tb in result.failures:
        status_map[test.id().split(".")[-1]] = ("❌ Failed", tb)
    for test, tb in result.errors:
        status_map[test.id().split(".")[-1]] = ("⚠️ Error", tb)

    test_status = [(i+1, name, status_map[name][0], status_map[name][1]) for i, name in enumerate(expected)]
    total = result.testsRun; failed = len(result.failures); errors = len(result.errors)
    passed = total - failed - errors
    return test_status, total, passed, failed, errors, output_text


def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk()
    root.title("Print Service Test Results")

    root.update_idletasks()
    w, h = 760, 560
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")

    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=10)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=420, anchor="w"); tree.column("Result", width=180, anchor="center")
    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    tk.Label(root, text="Console-like output").pack(padx=10, pady=(10, 0), anchor="w")
    box = tk.Text(root, height=14, wrap="word")
    box.insert("1.0", output_text); box.configure(state="disabled")
    box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    root.mainloop()


if __name__ == "__main__":
    show_results_gui()
