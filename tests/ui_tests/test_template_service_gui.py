import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import shutil
from services.auth_service import AuthService
from services.template_service import TemplateService

class TestTemplateService(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        # نقش‌ها: admin همه‌چیز، editor مدیریت قالب‌ها، viewer فقط دیدن
        self.auth.set_role_permissions("admin", ["*"])
        self.auth.set_role_permissions("editor", ["templates.manage", "templates.view", "templates.export"])
        self.auth.set_role_permissions("viewer", ["templates.view"])
        self.auth.register("admin", "adminpass", roles=["admin"])
        self.auth.register("ed", "edpass", roles=["editor"])
        self.auth.register("view", "viewpass", roles=["viewer"])

        # پوشهٔ موقت templates برای تست
        self.test_dir = os.path.join(os.getcwd(), "templates_test")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

        self.srv = TemplateService(auth_service=self.auth, templates_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_editor_create_update_delete(self):
        token = self.auth.authenticate("ed", "edpass")["token"]
        tpl = self.srv.create_template("Invoice A", {"layout": "A4"}, {"type": "invoice"}, actor_token=token)
        self.assertIn("template_id", tpl)
        tid = tpl["template_id"]
        # دریافت و بررسی
        got = self.srv.get_template(tid, actor_token=token)
        self.assertIsNotNone(got)
        self.assertEqual(got["name"], "Invoice A")
        # به‌روزرسانی
        up = self.srv.update_template(tid, {"name": "Invoice A v2", "meta": {"version": 2}}, actor_token=token)
        self.assertEqual(up["name"], "Invoice A v2")
        # حذف
        ok = self.srv.delete_template(tid, actor_token=token)
        self.assertTrue(ok)
        self.assertIsNone(self.srv.get_template(tid, actor_token=token))

    def test_viewer_cannot_manage_but_can_view(self):
        # editor ایجاد می‌کند
        ed_token = self.auth.authenticate("ed", "edpass")["token"]
        tpl = self.srv.create_template("Receipt", {"layout": "small"}, {}, actor_token=ed_token)
        tid = tpl["template_id"]
        # viewer می‌تواند لیست و مشاهده کند
        v_token = self.auth.authenticate("view", "viewpass")["token"]
        lst = self.srv.list_templates(actor_token=v_token)
        self.assertTrue(any(x["template_id"] == tid for x in lst))
        got = self.srv.get_template(tid, actor_token=v_token)
        self.assertEqual(got["name"], "Receipt")
        # viewer نباید بتواند حذف یا ویرایش کند
        with self.assertRaises(PermissionError):
            self.srv.update_template(tid, {"name": "X"}, actor_token=v_token)
        with self.assertRaises(PermissionError):
            self.srv.delete_template(tid, actor_token=v_token)

    def test_export_and_import(self):
        token = self.auth.authenticate("ed", "edpass")["token"]
        tpl = self.srv.create_template("ExportMe", {"layout": "A5"}, {}, actor_token=token)
        tid = tpl["template_id"]
        out_file = os.path.join(self.test_dir, "exported.json")
        path = self.srv.export_template(tid, out_file, actor_token=token)
        self.assertTrue(os.path.exists(path))
        # import as new
        imported = self.srv.import_template(path, actor_token=token)
        self.assertIn("template_id", imported)
        self.assertNotEqual(imported["template_id"], tid)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTemplateService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestTemplateService)
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
    root.title("Template Service Test Results")
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
