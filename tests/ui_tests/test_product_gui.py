import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.product import Product

class TestProductModel(unittest.TestCase):
    def setUp(self):
        self.product = Product(1, "Burger", 50.0, "Food", stock=10)

    def test_update_price_valid(self):
        self.product.update_price(60.0)
        self.assertEqual(self.product.price, 60.0)

    def test_update_price_invalid(self):
        with self.assertRaises(ValueError):
            self.product.update_price(-10)

    def test_update_name_valid(self):
        self.product.update_name("Cheese Burger")
        self.assertEqual(self.product.name, "Cheese Burger")

    def test_update_category_valid(self):
        self.product.update_category("FastFood")
        self.assertEqual(self.product.category, "FastFood")

    def test_edit_product_multiple(self):
        self.product.edit_product(name="Pizza", price=80.0, category="Italian", description="Thin crust")
        self.assertEqual(self.product.name, "Pizza")
        self.assertEqual(self.product.price, 80.0)
        self.assertEqual(self.product.category, "Italian")
        self.assertEqual(self.product.description, "Thin crust")

    def test_apply_discount_valid(self):
        self.product.apply_discount(20)
        self.assertEqual(self.product.price, 40.0)

    def test_update_stock(self):
        self.product.update_stock(-5)
        self.assertEqual(self.product.stock, 5)


def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProductModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestProductModel)
    status_map = {name: ("✅ Passed", "") for name in expected_names}

    for test, tb in result.failures:
        name = test.id().split(".")[-1]
        status_map[name] = ("❌ Failed", tb)

    for test, tb in result.errors:
        name = test.id().split(".")[-1]
        status_map[name] = ("⚠️ Error", tb)

    test_status = [(name, status_map[name][0], status_map[name][1]) for name in expected_names]

    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors

    return test_status, total, passed, failed, errors, output_text


def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()

    root = tk.Tk()
    root.title("Product Model Test Results")

    summary = tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    summary.pack(padx=10, pady=10, anchor="w")

    tree = ttk.Treeview(root, columns=("Test", "Result"), show="headings", height=10)
    tree.heading("Test", text="Test Case")
    tree.heading("Result", text="Result")
    tree.column("Test", width=260, anchor="w")
    tree.column("Result", width=140, anchor="center")

    for name, status, _ in test_status:
        tree.insert("", "end", values=(name, status))

    tree.pack(expand=True, fill="both", padx=10, pady=10)

    output_label = tk.Label(root, text="Console-like output")
    output_label.pack(padx=10, pady=(10, 0), anchor="w")

    output_box = tk.Text(root, height=12, wrap="word")
    output_box.insert("1.0", output_text)
    output_box.configure(state="disabled")
    output_box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    root.mainloop()


if __name__ == "__main__":
    show_results_gui()
