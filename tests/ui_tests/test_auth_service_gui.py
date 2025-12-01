import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
from services.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.srv = AuthService()
        # کاربر نمونه
        self.srv.register("admin", "secret123", roles=["admin", "user"])

    def test_register_and_list(self):
        u = self.srv.register("john", "passw0rd", roles=["user"])
        users = self.srv.list_users()
        self.assertTrue(any(x["username"] == "john" for x in users))

    def test_authenticate_and_token(self):
        res = self.srv.authenticate("admin", "secret123")
        self.assertIn("token", res)
        token = res["token"]
        user = self.srv.get_user_by_token(token)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")

    def test_change_password_and_logout(self):
        self.srv.register("alice", "oldpass")
        self.srv.change_password("alice", "oldpass", "newpass")
        res = self.srv.authenticate("alice", "newpass")
        token = res["token"]
        ok = self.srv.logout(token)
        self.assertTrue(ok)

    def test_has_role_and_delete(self):
        res = self.srv.authenticate("admin", "secret123")
        token = res["token"]
        self.assertTrue(self.srv.has_role(token, "admin"))
        self.assertTrue(self.srv.delete_user("admin"))
        self.assertIsNone(self.srv.get_user_by_token(token))

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestAuthService)
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
    root.title("Auth Service Test Results")
    root.update_idletasks()
    w, h = 720, 520
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=8)
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
