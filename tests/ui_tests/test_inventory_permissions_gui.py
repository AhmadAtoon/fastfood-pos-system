import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os

from services.auth_service import AuthService
from services.inventory_service import InventoryService

class TestInventoryPermissions(unittest.TestCase):
    def setUp(self):
        # سرویس احراز هویت و تنظیم نقش‌ها
        self.auth = AuthService()
        # نقش‌ها: admin همه‌چیز، cashier فقط ایجاد سفارش/رزرو
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("cashier", ["orders.reserve", "print.receipt"])
        # ثبت کاربران
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("cash", "cashpass", roles=["cashier"])

        # سرویس موجودی با اتصال به auth
        self.srv = InventoryService(auth_service=self.auth)
        # افزودن آیتم‌ها
        self.srv.upsert_item("FOOD-001", "Burger", 10, 120000, {"category": "food"})
        self.srv.upsert_item("DRINK-002", "Soda", 5, 20000, {"category": "drink"})

    def test_admin_adjust_and_reserve(self):
        # admin توکن می‌گیرد
        res = self.auth.authenticate("admin", "adminpass")
        token = res["token"]
        # admin می‌تواند موجودی را تنظیم کند
        tx = self.srv.adjust_stock("FOOD-001", -2, reason="waste", actor_token=token)
        self.assertTrue(tx["final_stock"] <= 8)
        # admin می‌تواند رزرو کند
        r = self.srv.reserve_for_order("ORD-900", [{"sku": "DRINK-002", "qty": 2}], actor_token=token)
        self.assertEqual(len(r["reserved"]), 1)
        # commit با admin
        c = self.srv.commit_order("ORD-900", actor_token=token)
        self.assertEqual(len(c["committed"]), 1)

    def test_cashier_cannot_adjust_but_can_reserve(self):
        res = self.auth.authenticate("cash", "cashpass")
        token = res["token"]
        # cashier نباید بتواند adjust_stock انجام دهد
        with self.assertRaises(PermissionError):
            self.srv.adjust_stock("FOOD-001", -1, reason="waste", actor_token=token)
        # cashier می‌تواند رزرو کند (طبق نقش تعریف‌شده)
        r = self.srv.reserve_for_order("ORD-901", [{"sku": "FOOD-001", "qty": 1}], actor_token=token)
        self.assertEqual(len(r["reserved"]), 1)
        # اما cashier نباید commit کند (نیاز به مجوز commit)
        with self.assertRaises(PermissionError):
            self.srv.commit_order("ORD-901", actor_token=token)

    def test_transactions_and_list(self):
        # بدون توکن می‌توان لیست آیتم‌ها و تراکنش‌ها را خواند
        items = self.srv.list_items()
        self.assertGreaterEqual(len(items), 2)
        # تراکنش‌ها در ابتدا خالی‌اند
        txs = self.srv.transactions()
        self.assertIsInstance(txs, list)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInventoryPermissions)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestInventoryPermissions)
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
    root.title("Inventory Permissions Test Results")

    root.update_idletasks()
    w, h = 780, 580
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")

    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=10)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=440, anchor="w"); tree.column("Result", width=180, anchor="center")
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
