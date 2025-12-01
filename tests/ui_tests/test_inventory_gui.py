import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.product import Product
from models.inventory import Inventory

class TestInventoryModel(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()
        self.burger = Product(1, "Burger", 50.0, "Food", stock=10)
        self.pizza = Product(2, "Pizza", 80.0, "Food", stock=5)
        self.drink = Product(3, "Soda", 20.0, "Drink", stock=50)

    def test_add_product(self):
        self.inventory.add_product(self.burger, 10)
        self.assertEqual(self.inventory.products[1]["quantity"], 10)

    def test_update_stock(self):
        self.inventory.add_product(self.pizza, 5)
        self.inventory.update_stock(2, 8)
        self.assertEqual(self.inventory.products[2]["quantity"], 8)

    def test_remove_product(self):
        self.inventory.add_product(self.drink, 20)
        self.inventory.remove_product(3)
        self.assertNotIn(3, self.inventory.products)

    def test_check_availability(self):
        self.inventory.add_product(self.burger, 10)
        self.assertTrue(self.inventory.check_availability(1, 5))
        self.assertFalse(self.inventory.check_availability(1, 20))

    def test_low_stock_alert(self):
        self.inventory.add_product(self.burger, 2)
        self.inventory.add_product(self.pizza, 10)
        alerts = self.inventory.low_stock_alert(5)
        self.assertIn(1, alerts)
        self.assertNotIn(2, alerts)

    def test_calculate_inventory_value(self):
        self.inventory.add_product(self.burger, 2)  # 100
        self.inventory.add_product(self.drink, 5)  # 100
        self.assertEqual(self.inventory.calculate_inventory_value(), 200.0)

    def test_generate_inventory_report(self):
        self.inventory.add_product(self.burger, 2)
        report = self.inventory.generate_inventory_report()
        self.assertIn("Burger", report)
        self.assertIn("Total Inventory Value", report)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInventoryModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestInventoryModel)
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
    root.title("Inventory Model Test Results")

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
    output_box = tk.Text(root, height=12, wrap="word")
    output_box.insert("1.0", output_text)
    output_box.configure(state="disabled")
    output_box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    footer = tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}")
    footer.pack(padx=10, pady=10, anchor="w")

    root.mainloop()

if __name__ == "__main__":
    show_results_gui()
