# tests/ui_tests/test_analytics_service_gui.py
import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil
import time

from services.auth_service import AuthService
from services.analytics_service import AnalyticsService

class TestAnalyticsService(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("analyst", ["analytics.view", "analytics.manage"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("ana", "analystpass", roles=["analyst"])

        self.test_dir = os.path.join(os.getcwd(), "analytics_test")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

        self.srv = AnalyticsService(auth_service=self.auth, storage_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_record_and_aggregates_by_analyst(self):
        token = self.auth.authenticate("ana", "analystpass")["token"]
        # ثبت چند رویداد سفارش و پرداخت
        now = int(time.time())
        self.srv.record_event("order", {"order_id": "O1", "totals": {"grand_total": 100}}, actor_token=token)
        time.sleep(1)
        self.srv.record_event("order", {"order_id": "O2", "totals": {"grand_total": 200}}, actor_token=token)
        self.srv.record_event("payment", {"tx_id": "T1", "amount": 300}, actor_token=token)
        # خلاصه فروش
        sales = self.srv.sales_by_day(actor_token=token)
        self.assertTrue(isinstance(sales, dict))
        # تعداد سفارش‌ها
        counts = self.srv.orders_count_by_day(actor_token=token)
        self.assertTrue(sum(counts.values()) >= 2)

    def test_top_items(self):
        token = self.auth.authenticate("ana", "analystpass")["token"]
        # ثبت سفارش با خطوط
        self.srv.record_event("order", {"order_id": "O3", "lines": [{"name": "Burger", "qty": 3}, {"name": "Soda", "qty": 1}]}, actor_token=token)
        self.srv.record_event("order", {"order_id": "O4", "lines": [{"name": "Burger", "qty": 2}]}, actor_token=token)
        top = self.srv.top_items(top_n=2, actor_token=token)
        self.assertTrue(any(item[0] == "Burger" for item in top))

    def test_permission_denied_for_view(self):
        # کاربر بدون مجوز view
        self.auth.register("bob", "bobpass", roles=["user"])
        bob_token = self.auth.authenticate("bob", "bobpass")["token"]
        with self.assertRaises(PermissionError):
            self.srv.list_events(actor_token=bob_token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalyticsService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestAnalyticsService)
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
    root.title("Analytics Service Test Results")
    root.update_idletasks()
    w, h = 760, 520
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=8)
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
