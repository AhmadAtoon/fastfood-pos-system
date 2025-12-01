import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from services.auth_service import AuthService

class TestAuthPermissions(unittest.TestCase):
    def setUp(self):
        self.srv = AuthService()
        # تنظیم نقش‌ها و مجوزها برای تست
        # در این تست admin را با '*' تنظیم می‌کنیم تا همهٔ مجوزها را داشته باشد
        self.srv.set_role_permissions("admin", ["*"])
        self.srv.set_role_permissions("cashier", ["orders.create", "print.receipt"])
        # ثبت کاربران
        self.srv.register("admin", "adminpass", roles=["admin"])
        self.srv.register("cash", "cashpass", roles=["cashier"])

    def test_auth_and_permissions(self):
        res_admin = self.srv.authenticate("admin", "adminpass")
        token_admin = res_admin["token"]
        res_cash = self.srv.authenticate("cash", "cashpass")
        token_cash = res_cash["token"]

        # admin باید همه‌چیز داشته باشد (با '*' که قرار داده‌ایم)
        self.assertTrue(self.srv.has_permission(token_admin, "orders.create"))
        self.assertTrue(self.srv.has_permission(token_admin, "inventory.adjust"))
        # cashier محدود است
        self.assertTrue(self.srv.has_permission(token_cash, "orders.create"))
        self.assertFalse(self.srv.has_permission(token_cash, "inventory.adjust"))

    def test_get_permissions_for_user(self):
        res = self.srv.authenticate("cash", "cashpass")
        token = res["token"]
        perms = self.srv.get_permissions_for_user(token)
        self.assertIn("orders.create", perms)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthPermissions)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestAuthPermissions)
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
    root.title("Auth Permissions Test Results")
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
