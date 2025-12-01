import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil
from services.reporting_service import ReportingService
from services.auth_service import AuthService

# providers نمونه
def orders_provider():
    return {
        "orders": [
            {"order_id": "O1", "created_at": int(time.time()) - 86400, "totals": {"grand_total": 100}},
            {"order_id": "O2", "created_at": int(time.time()), "totals": {"grand_total": 200}},
        ]
    }

def inventory_provider():
    return {
        "items": [
            {"sku": "FOOD-001", "name": "Burger", "stock": 2},
            {"sku": "DRINK-002", "name": "Soda", "stock": 10},
        ]
    }

class TestReportingService(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("analyst", ["reports.view", "reports.export"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("ana", "analystpass", roles=["analyst"])

        self.rsrv = ReportingService(auth_service=self.auth)
        self.rsrv.register_data_provider("orders", orders_provider)
        self.rsrv.register_data_provider("inventory", inventory_provider)

        self.out_dir = os.path.join(os.getcwd(), "reports_out")
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)
        os.makedirs(self.out_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_generate_and_export_by_admin(self):
        token = self.auth.authenticate("admin", "adminpass")["token"]
        rpt = self.rsrv.generate_report("sales_summary", {}, actor_token=token)
        self.assertIn("report_id", rpt)
        # export json
        out_json = os.path.join(self.out_dir, "sales_admin.json")
        path = self.rsrv.export_report(rpt, "json", out_json, actor_token=token)
        self.assertTrue(os.path.exists(path))
        # export csv
        out_csv = os.path.join(self.out_dir, "sales_admin.csv")
        path2 = self.rsrv.export_report(rpt, "csv", out_csv, actor_token=token)
        self.assertTrue(os.path.exists(path2))

    def test_analyst_can_view_and_export(self):
        token = self.auth.authenticate("ana", "analystpass")["token"]
        rpt = self.rsrv.generate_report("inventory_status", {"threshold": 5}, actor_token=token)
        self.assertIn("report_id", rpt)
        out_csv = os.path.join(self.out_dir, "inventory_ana.csv")
        path = self.rsrv.export_report(rpt, "csv", out_csv, actor_token=token)
        self.assertTrue(os.path.exists(path))

    def test_no_permission_denied(self):
        # کاربری بدون مجوز
        self.auth.register("bob", "bobpass", roles=["user"])
        token = self.auth.authenticate("bob", "bobpass")["token"]
        with self.assertRaises(PermissionError):
            self.rsrv.generate_report("sales_summary", {}, actor_token=token)
        # حتی export بدون مجوز باید رد شود
        # ساخت گزارش با admin و تلاش export با bob
        admin_token = self.auth.authenticate("admin", "adminpass")["token"]
        rpt = self.rsrv.generate_report("sales_summary", {}, actor_token=admin_token)
        out = os.path.join(self.out_dir, "bad_export.csv")
        with self.assertRaises(PermissionError):
            self.rsrv.export_report(rpt, "csv", out, actor_token=token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReportingService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestReportingService)
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
    root.title("Reporting Service Test Results")
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
