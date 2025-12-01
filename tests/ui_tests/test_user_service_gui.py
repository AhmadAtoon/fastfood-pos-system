import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO

from services.auth_service import AuthService
from services.user_service import UserService

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        # ثبت کاربر در AuthService
        self.auth.register("john", "pass123", roles=["user"])
        self.usrv = UserService(auth_service=self.auth)

    def test_create_and_get_profile(self):
        prof = self.usrv.create_profile("john", "John Doe", "john@example.com")
        self.assertEqual(prof["username"], "john")
        got = self.usrv.get_profile("john")
        self.assertIsNotNone(got)
        self.assertEqual(got["email"], "john@example.com")

    def test_update_and_list(self):
        self.usrv.create_profile("john", "John Doe", "john@example.com")
        self.usrv.update_profile("john", {"full_name": "John X Doe"})
        lst = self.usrv.list_profiles({"name_contains": "x"})
        self.assertTrue(any(p["username"] == "john" for p in lst))

    def test_assign_and_remove_roles(self):
        self.usrv.create_profile("john", "John Doe", "john@example.com")
        updated = self.usrv.assign_roles("john", ["manager"])
        self.assertIn("manager", updated["roles"])
        updated2 = self.usrv.remove_roles("john", ["manager"])
        self.assertNotIn("manager", updated2["roles"])

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUserService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestUserService)
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
    root.title("User Service Test Results")
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
