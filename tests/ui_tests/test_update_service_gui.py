import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil
from services.update_service import UpdateService

# provider نمونه شبیه‌سازی‌شده
def provider_alpha():
    return {"version": "1.2.0", "notes": "Bug fixes and improvements", "url": "http://example.com/alpha"}

def provider_beta():
    return {"version": "2.0.0", "notes": "Major release", "url": "http://example.com/beta"}

class TestUpdateService(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), "updates_test")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)
        self.srv = UpdateService(updates_dir=self.test_dir)
        self.srv.register_update_provider("alpha", provider_alpha)
        self.srv.register_update_provider("beta", provider_beta)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_and_download_and_apply(self):
        avail = self.srv.check_for_updates()
        self.assertTrue(any(x.get("provider") == "alpha" for x in avail))
        # دانلود نسخه alpha
        dl = self.srv.download_update("alpha", "1.2.0")
        self.assertIn("update_id", dl)
        # فهرست دانلودها
        lst = self.srv.list_updates()
        self.assertTrue(any("alpha" in x.get("file","") for x in lst))
        # اعمال به‌روزرسانی
        ok = self.srv.apply_update(dl["update_id"])
        self.assertTrue(ok)
        hist = self.srv.get_update_history()
        self.assertGreaterEqual(len(hist), 1)
        self.assertEqual(hist[-1]["provider"], "alpha")

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestUpdateService)
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
    root.title("Update Service Test Results")
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
