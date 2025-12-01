# tests/ui_tests/test_notification_service_gui.py
import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil
import time

from services.auth_service import AuthService
from services.notification_service import NotificationService

class TestNotificationService(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("notifier", ["notify.send", "notify.manage"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("noti", "notipass", roles=["notifier"])
        self.auth.register("bob", "bobpass", roles=["user"])

        self.test_dir = os.path.join(os.getcwd(), "notifications_test")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

        self.srv = NotificationService(auth_service=self.auth, storage_dir=self.test_dir)
        # listener نمونه که یک فایل لاگ جدا می‌نویسد
        def listener(ev):
            p = os.path.join(self.test_dir, f"listener_{ev.get('id')}.json")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(str(ev.get("type")))
        self.srv.register_listener(listener)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_send_internal_and_webhook_by_notifier(self):
        token = self.auth.authenticate("noti", "notipass")["token"]
        r = self.srv.send_internal("Hello", "Body text", {"k": "v"}, actor_token=token)
        self.assertEqual(r["type"], "internal")
        # وبهوک
        w = self.srv.send_webhook("http://example.com/hook", {"a": 1}, actor_token=token)
        self.assertEqual(w["type"], "webhook")
        # فایل وبهوک باید وجود داشته باشد
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, w["file"])))
        # listener فایل لاگ ساخته باشد
        self.assertTrue(any(fn.startswith("listener_") for fn in os.listdir(self.test_dir)))

    def test_queue_and_process_requires_manage(self):
        token = self.auth.authenticate("noti", "notipass")["token"]
        qid = self.srv.queue_notification({"title": "Q1", "body": "queued"})
        # بدون manage نباید پردازش شود اگر actor_token نداشته باشیم
        with self.assertRaises(PermissionError):
            self.srv.process_queue(actor_token=None)
        # با توکن manage پردازش می‌شود
        processed = self.srv.process_queue(actor_token=token)
        self.assertTrue(any(p.get("title") == "Q1" for p in processed))

    def test_permission_denied_for_user(self):
        token = self.auth.authenticate("bob", "bobpass")["token"]
        with self.assertRaises(PermissionError):
            self.srv.send_internal("X", "Y", actor_token=token)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNotificationService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestNotificationService)
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
    root.title("Notification Service Test Results")
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
