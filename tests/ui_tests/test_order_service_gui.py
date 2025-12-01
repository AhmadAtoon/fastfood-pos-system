# tests/ui_tests/test_order_service_gui.py
import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil
import time

from services.auth_service import AuthService
from services.notification_service import NotificationService
from services.analytics_service import AnalyticsService
from services.order_service import make_order_service

class TestOrderServicePermissions(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("cashier", ["orders.create", "orders.view"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("cash", "cashpass", roles=["cashier"])

        # سرویس‌های کمکی
        self.notif_dir = os.path.join(os.getcwd(), "notifications_test_order")
        if os.path.exists(self.notif_dir):
            shutil.rmtree(self.notif_dir)
        os.makedirs(self.notif_dir, exist_ok=True)
        self.notif = NotificationService(auth_service=self.auth, storage_dir=self.notif_dir)
        self.analytics = AnalyticsService(auth_service=self.auth, storage_dir=os.path.join(os.getcwd(), "analytics_test_order"))

        # ساخت OrderService با factory تا دکوراتورها متصل شوند
        self.srv = make_order_service(auth_service=self.auth, notification_service=self.notif, analytics_service=self.analytics)

    def tearDown(self):
        if os.path.exists(self.notif_dir):
            shutil.rmtree(self.notif_dir)
        if os.path.exists(os.path.join(os.getcwd(), "analytics_test_order")):
            shutil.rmtree(os.path.join(os.getcwd(), "analytics_test_order"))

    def test_admin_create_update_cancel_and_events(self):
        token = self.auth.authenticate("admin", "adminpass")["token"]
        o = self.srv.create_order({"customer_id": 101, "lines": [{"sku":"FOOD-1","qty":2,"price":100}]}, actor_token=token)
        oid = o["order_id"]
        self.assertIsNotNone(oid)
        # بررسی اینکه analytics یک event ثبت کرده
        events = self.analytics.list_events(actor_token=token)
        self.assertTrue(any(e.get("type") == "order.created" or e.get("type") == "order" for e in events))
        # به‌روزرسانی
        up = self.srv.update_order(oid, {"meta": {"note": "urgent"}}, actor_token=token)
        self.assertEqual(up["meta"].get("note"), "urgent")
        # کنسل کردن
        c = self.srv.cancel_order(oid, reason="customer", actor_token=token)
        self.assertEqual(c["status"], "cancelled")

    def test_cashier_create_but_cannot_cancel(self):
        token = self.auth.authenticate("cash", "cashpass")["token"]
        o = self.srv.create_order({"customer_id": 202, "lines": [{"sku":"DR-1","qty":1,"price":50}]}, actor_token=token)
        oid = o["order_id"]
        self.assertIsNotNone(oid)
        got = self.srv.get_order(oid, actor_token=token)
        self.assertEqual(got["order_id"], oid)
        with self.assertRaises(PermissionError):
            self.srv.cancel_order(oid, reason="test", actor_token=token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderServicePermissions)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestOrderServicePermissions)
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
    root.title("Order Service Test Results (final)")
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
