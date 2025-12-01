# tests/ui_tests/test_payment_service_gui.py
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
from services.payment_service import make_payment_service

class TestPaymentService(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("cashier", ["payments.process"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("cash", "cashpass", roles=["cashier"])

        self.notif_dir = os.path.join(os.getcwd(), "notifications_test_payment")
        if os.path.exists(self.notif_dir):
            shutil.rmtree(self.notif_dir)
        os.makedirs(self.notif_dir, exist_ok=True)
        self.notif = NotificationService(auth_service=self.auth, storage_dir=self.notif_dir)
        self.analytics = AnalyticsService(auth_service=self.auth, storage_dir=os.path.join(os.getcwd(), "analytics_test_payment"))

        self.psrv = make_payment_service(auth_service=self.auth, notification_service=self.notif, analytics_service=self.analytics)

    def tearDown(self):
        if os.path.exists(self.notif_dir):
            shutil.rmtree(self.notif_dir)
        if os.path.exists(os.path.join(os.getcwd(), "analytics_test_payment")):
            shutil.rmtree(os.path.join(os.getcwd(), "analytics_test_payment"))

    def test_admin_process_and_refund_and_events(self):
        token = self.auth.authenticate("admin", "adminpass")["token"]
        tx = self.psrv.process_payment(order_id="ORD-1", amount=150000, currency="IRR", actor_token=token)
        self.assertEqual(tx["type"], "charge")
        tx_id = tx["tx_id"]
        # بررسی ثبت event در analytics
        events = self.analytics.list_events(actor_token=token)
        self.assertTrue(any(e.get("type") == "payment.processed" or e.get("type") == "payment" for e in events))
        # بازپرداخت کامل
        rf = self.psrv.refund_payment(tx_id, actor_token=token)
        self.assertEqual(rf["type"], "refund")
        orig = self.psrv.get_transaction(tx_id, actor_token=token)
        self.assertEqual(orig["status"], "refunded")

    def test_cashier_can_process_but_cannot_refund(self):
        token = self.auth.authenticate("cash", "cashpass")["token"]
        tx = self.psrv.process_payment(order_id="ORD-2", amount=50000, currency="IRR", actor_token=token)
        self.assertEqual(tx["type"], "charge")
        tx_id = tx["tx_id"]
        with self.assertRaises(PermissionError):
            self.psrv.refund_payment(tx_id, actor_token=token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPaymentService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestPaymentService)
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
    root.title("Payment Service Test Results (final)")
    root.update_idletasks()
    w, h = 720, 480
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=6)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=420, anchor="w"); tree.column("Result", width=180, anchor="center")
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
