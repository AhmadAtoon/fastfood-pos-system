import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil

from services.backup_service import BackupService

# providers نمونه
def orders_provider():
    return {
        "orders": [
            {"order_id": "O1", "total": 100},
            {"order_id": "O2", "total": 200}
        ]
    }

def inventory_provider():
    return {
        "items": [
            {"sku": "FOOD-001", "stock": 100},
            {"sku": "DRINK-002", "stock": 150}
        ]
    }

class TestBackupService(unittest.TestCase):
    def setUp(self):
        # پوشهٔ موقت برای تست
        self.test_dir = os.path.join(os.getcwd(), "backups_test")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)
        self.srv = BackupService(backup_dir=self.test_dir)
        self.srv.register_provider("orders", orders_provider)
        self.srv.register_provider("inventory", inventory_provider)
        self.restored = {}

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_list_and_get_backup(self):
        meta = self.srv.create_backup(label="test1")
        self.assertIn("backup_id", meta)
        lst = self.srv.list_backups()
        self.assertGreaterEqual(len(lst), 1)
        # خواندن محتوا
        payload = self.srv.get_backup(meta["backup_id"])
        self.assertIsNotNone(payload)
        self.assertIn("data", payload)
        self.assertIn("orders", payload["data"])

    def test_restore_and_verify_and_delete(self):
        meta = self.srv.create_backup(label="test2")
        bid = meta["backup_id"]
        ok = self.srv.verify_backup(bid)
        self.assertTrue(ok)
        # callback نمونه برای بازیابی
        def cb(name, data):
            self.restored[name] = data
        self.srv.restore_backup(bid, cb)
        self.assertIn("orders", self.restored)
        # حذف
        deleted = self.srv.delete_backup(bid)
        self.assertTrue(deleted)
        # بعد از حذف نباید پیدا شود
        self.assertIsNone(self.srv.get_backup(bid))

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBackupService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestBackupService)
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
    root.title("Backup Service Test Results")
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
