# tests/ui_tests/test_user_gui.py
import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO

from models.user import User

class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.user = User(1, "ahmad", "1234", "admin", "ahmad@example.com")

    def test_check_password_correct(self):
        self.assertTrue(self.user.check_password("1234"))

    def test_check_password_incorrect(self):
        self.assertFalse(self.user.check_password("wrong"))

    def test_is_admin_true(self):
        self.assertTrue(self.user.is_admin())

    def test_is_admin_false(self):
        user2 = User(2, "ali", "abcd", "cashier")
        self.assertFalse(user2.is_admin())

    def test_activation_cycle(self):
        self.user.deactivate()
        self.assertFalse(self.user.active)
        self.user.activate()
        self.assertTrue(self.user.active)

    def test_change_password_valid(self):
        self.user.change_password("abcd")
        self.assertTrue(self.user.check_password("abcd"))

    def test_change_password_invalid(self):
        with self.assertRaises(ValueError):
            self.user.change_password("123")  # کمتر از 4 کاراکتر


def run_suite_and_collect():
    # نام تست‌ها را امن از کلاس استخراج می‌کنیم
    expected_names = unittest.TestLoader().getTestCaseNames(TestUserModel)  # list[str]

    suite = unittest.TestLoader().loadTestsFromTestCase(TestUserModel)

    # گرفتن خروجی مشابه کنسول
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    # ساخت نگاشت نام‌ها به وضعیت
    status_map = {name: ("✅ Passed", "") for name in expected_names}

    # اعمال Failures و Errors
    for test, tb in result.failures:
        name = test.id().split(".")[-1]
        status_map[name] = ("❌ Failed", tb)

    for test, tb in result.errors:
        name = test.id().split(".")[-1]
        status_map[name] = ("⚠️ Error", tb)

    # تبدیل به لیست برای جدول
    test_status = [(name, status_map[name][0], status_map[name][1]) for name in expected_names]

    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors

    return test_status, total, passed, failed, errors, output_text


def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()

    root = tk.Tk()
    root.title("User model test results")

    # خلاصه کلی
    summary = tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    summary.pack(padx=10, pady=10, anchor="w")

    # جدول نتایج
    tree = ttk.Treeview(root, columns=("Test", "Result"), show="headings", height=10)
    tree.heading("Test", text="Test case")
    tree.heading("Result", text="Result")
    tree.column("Test", width=260, anchor="w")
    tree.column("Result", width=140, anchor="center")

    for name, status, _ in test_status:
        tree.insert("", "end", values=(name, status))

    tree.pack(expand=True, fill="both", padx=10, pady=10)

    # بخش جزئیات
    detail_label = tk.Label(root, text="Details")
    detail_label.pack(padx=10, pady=(10, 0), anchor="w")

    detail_text = tk.Text(root, height=10, wrap="word")
    detail_text.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    def on_select(event):
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])
        name = item["values"][0]
        for n, status, detail in test_status:
            if n == name:
                detail_text.delete("1.0", tk.END)
                detail_text.insert(tk.END, detail if detail else "No details (Passed).")
                break

    tree.bind("<<TreeviewSelect>>", on_select)

    # خروجی کامل کنسولی (مثل پاورشل)
    output_label = tk.Label(root, text="Console-like output")
    output_label.pack(padx=10, pady=(10, 0), anchor="w")

    output_box = tk.Text(root, height=12, wrap="word")
    output_box.insert("1.0", output_text)
    output_box.configure(state="disabled")
    output_box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    root.mainloop()


if __name__ == "__main__":
    show_results_gui()
