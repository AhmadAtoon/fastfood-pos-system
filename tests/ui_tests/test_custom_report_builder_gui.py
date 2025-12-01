import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from reports.custom_report_builder import CustomReportBuilder

class TestCustomReportBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = CustomReportBuilder()
        self.builder.add_section("Sales", lambda: "Total Sales: 200$")
        self.builder.add_section("Inventory", lambda: "Low Stock: Soda")
        self.builder.add_section("Tax", lambda: "Tax Payable: 18$")

    def test_build_report(self):
        report = self.builder.build_report()
        self.assertIn("Sales", report)
        self.assertIn("Inventory", report)
        self.assertIn("Tax", report)

    def test_render_text_report(self):
        txt = self.builder.render_text_report()
        self.assertIn("Custom Report", txt)
        self.assertIn("[Sales]", txt)
        self.assertIn("[Inventory]", txt)
        self.assertIn("[Tax]", txt)

# -------------------------------
# اجرای تست‌ها و نمایش گرافیکی
# -------------------------------
def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomReportBuilder)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestCustomReportBuilder)
    status_map = {name: ("✅ Passed", "") for name in expected_names}
    for test, tb in result.failures:
        name = test.id().split(".")[-1]
        status_map[name] = ("❌ Failed", tb)
    for test, tb in result.errors:
        name = test.id().split(".")[-1]
        status_map[name] = ("⚠️ Error", tb)

    test_status = [(i+1, name, status_map[name][0], status_map[name][1]) for i, name in enumerate(expected_names)]
    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors
    return test_status, total, passed, failed, errors, output_text

def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk()
    root.title("Custom Report Builder Test Results")

    # پنجره در وسط صفحه باز شود
    root.update_idletasks()
    w, h = 600, 500
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    summary = tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    summary.pack(padx=10, pady=10, anchor="w")

    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=10)
    tree.heading("No", text="#")
    tree.heading("Test", text="Test Case")
    tree.heading("Result", text="Result")
    tree.column("No", width=40, anchor="center")
    tree.column("Test", width=280, anchor="w")
    tree.column("Result", width=120, anchor="center")

    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    output_label = tk.Label(root, text="Console-like output")
    output_label.pack(padx=10, pady=(10, 0), anchor="w")
    output_box = tk.Text(root, height=14, wrap="word")
    output_box.insert("1.0", output_text)
    output_box.configure(state="disabled")
    output_box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    footer = tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}")
    footer.pack(padx=10, pady=10, anchor="w")

    root.mainloop()

if __name__ == "__main__":
    show_results_gui()
