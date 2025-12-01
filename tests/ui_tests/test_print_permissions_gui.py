import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil

from services.auth_service import AuthService
from services.print_service import PrintService

ORDER_SAMPLE = {
    "order_id": "ORD-123",
    "customer_id": 1001,
    "status": "paid",
    "created_at": 1732886400,
    "items": [
        {"product_id": 1, "name": "Burger", "qty": 2, "price": 120000},
        {"product_id": 2, "name": "Soda", "qty": 1, "price": 20000},
    ],
    "totals": {
        "subtotal": 260000,
        "discount_total": 0,
        "tax": 23400,
        "grand_total": 283400,
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
        {"name": "Burger", "qty": 2, "price": 120000, "discount": 0, "line_total": 240000},
        {"name": "Soda", "qty": 1, "price": 20000, "discount": 0, "line_total": 20000},
    ],
    "totals": ORDER_SAMPLE["totals"],
}

class TestPrintPermissions(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        # نقش‌ها: admin همه‌چیز، cashier فقط رسید و تیکت آشپزخانه
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("cashier", ["print.receipt", "print.kitchen"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("cash", "cashpass", roles=["cashier"])

        self.psrv = PrintService(auth_service=self.auth)
        # فایل‌های خروجی تست را در پوشهٔ temp قرار می‌دهیم
        self.out_dir = os.path.join(os.getcwd(), "print_test_out")
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)
        os.makedirs(self.out_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_admin_can_print_all(self):
        token = self.auth.authenticate("admin", "adminpass")["token"]
        p1 = os.path.join(self.out_dir, "inv_admin.pdf")
        p2 = os.path.join(self.out_dir, "kitchen_admin.pdf")
        p3 = os.path.join(self.out_dir, "receipt_admin.pdf")
        self.psrv.print_invoice(INVOICE_SAMPLE, p1, actor_token=token)
        self.psrv.print_kitchen_ticket(ORDER_SAMPLE, p2, actor_token=token)
        self.psrv.print_receipt(ORDER_SAMPLE, p3, actor_token=token)
        self.assertTrue(os.path.exists(p1))
        self.assertTrue(os.path.exists(p2))
        self.assertTrue(os.path.exists(p3))

    def test_cashier_limited_prints(self):
        token = self.auth.authenticate("cash", "cashpass")["token"]
        p_receipt = os.path.join(self.out_dir, "receipt_cash.pdf")
        p_kitchen = os.path.join(self.out_dir, "kitchen_cash.pdf")
        p_invoice = os.path.join(self.out_dir, "inv_cash.pdf")
        # cashier می‌تواند رسید و تیکت آشپزخانه چاپ کند
        self.psrv.print_receipt(ORDER_SAMPLE, p_receipt, actor_token=token)
        self.psrv.print_kitchen_ticket(ORDER_SAMPLE, p_kitchen, actor_token=token)
        self.assertTrue(os.path.exists(p_receipt))
        self.assertTrue(os.path.exists(p_kitchen))
        # اما نباید فاکتور رسمی چاپ کند
        with self.assertRaises(PermissionError):
            self.psrv.print_invoice(INVOICE_SAMPLE, p_invoice, actor_token=token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPrintPermissions)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestPrintPermissions)
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
    root.title("Print Permissions Test Results")
    root.update_idletasks()
    w, h = 760, 520
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=6)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=480, anchor="w"); tree.column("Result", width=160, anchor="center")
    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    tk.Label(root, text="Console-like output").pack(padx=10, pady=(10, 0), anchor="w")
    box = tk.Text(root, height=10, wrap="word")
    box.insert("1.0", output_text); box.configure(state="disabled")
    box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    root.mainloop()

if __name__ == "__main__":
    show_results_gui()
