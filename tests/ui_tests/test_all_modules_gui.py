import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import pkgutil
import importlib
import tests.ui_tests

def run_all_tests():
    # بارگذاری همه‌ی ماژول‌های تست داخل پوشه ui_tests
    suite = unittest.TestSuite()
    for loader, module_name, is_pkg in pkgutil.iter_modules(tests.ui_tests.__path__):
        if module_name.startswith("test_"):  # فقط فایل‌های تست
            module = importlib.import_module(f"tests.ui_tests.{module_name}")
            suite.addTests(unittest.TestLoader().loadTestsFromModule(module))

    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    # جمع‌آوری وضعیت تست‌ها
    test_status = []
    for i, test in enumerate(result.testsRun and suite, start=1):
        # اینجا فقط تعداد کلی رو نمایش می‌دیم
        pass

    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors

    return total, passed, failed, errors, output_text

def show_results_gui():
    total, passed, failed, errors, output_text = run_all_tests()

    root = tk.Tk()
    root.title("All Modules Test Results")

    summary = tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    summary.pack(padx=10, pady=10, anchor="w")

    output_label = tk.Label(root, text="Console-like output")
    output_label.pack(padx=10, pady=(10, 0), anchor="w")

    output_box = tk.Text(root, height=25, wrap="word")
    output_box.insert("1.0", output_text)
    output_box.configure(state="disabled")
    output_box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    footer = tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}")
    footer.pack(padx=10, pady=10, anchor="w")

    root.mainloop()

if __name__ == "__main__":
    show_results_gui()
