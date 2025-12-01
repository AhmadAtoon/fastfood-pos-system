# tests/ui_tests/test_auth_decorators_gui.py
import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import inspect

from services.auth_service import AuthService
from services.auth_decorators import requires_permission

class DummyService:
    def __init__(self):
        pass

    # متدی که actor_token را به صورت positional می‌گیرد
    def do_positional(self, data, actor_token):
        return {"ok": True, "data": data}

    # متدی که actor_token را به صورت keyword می‌گیرد
    def do_keyword(self, data, actor_token=None):
        return {"ok": True, "data": data}

class TestAuthDecorators(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("limited", ["svc.use"])
        self.auth.register("admin", "apass", roles=["admin"])
        self.auth.register("lim", "lpass", roles=["limited"])

        self.ds = DummyService()
        # بستن دکوراتورها با auth واقعی و permission مناسب
        self.ds.do_positional = requires_permission(self.auth, "svc.use")(self.ds.do_positional)
        self.ds.do_keyword = requires_permission(self.auth, "svc.use")(self.ds.do_keyword)

    def test_positional_token_allows(self):
        token = self.auth.authenticate("lim", "lpass")["token"]
        # فراخوانی با positional token
        res = self.ds.do_positional({"x": 1}, token)
        self.assertTrue(res["ok"])

    def test_keyword_token_allows(self):
        token = self.auth.authenticate("lim", "lpass")["token"]
        res = self.ds.do_keyword({"x": 2}, actor_token=token)
        self.assertTrue(res["ok"])

    def test_missing_token_denied(self):
        with self.assertRaises(PermissionError):
            self.ds.do_keyword({"x": 3})  # بدون token

    def test_wrong_permission_denied(self):
        # کاربری بدون permission مناسب
        self.auth.register("bob", "bobpass", roles=["user"])
        bob_token = self.auth.authenticate("bob", "bobpass")["token"]
        with self.assertRaises(PermissionError):
            self.ds.do_keyword({"x": 4}, actor_token=bob_token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthDecorators)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestAuthDecorators)
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
    root.title("Auth Decorators Test Results")
    root.update_idletasks()
    w, h = 640, 420
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=6)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=380, anchor="w"); tree.column("Result", width=150, anchor="center")
    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    tk.Label(root, text="Console-like output").pack(padx=10, pady=(10, 0), anchor="w")
    box = tk.Text(root, height=8, wrap="word")
    box.insert("1.0", output_text); box.configure(state="disabled")
    box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    root.mainloop()

if __name__ == "__main__":
    show_results_gui()
