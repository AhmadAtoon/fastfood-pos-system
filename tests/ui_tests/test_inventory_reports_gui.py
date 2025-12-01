import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.product import Product
from models.customer import Customer
from models.order import Order
from models.inventory import Inventory
from reports.inventory_reports import InventoryReports

class TestInventoryReports(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.burger = Product(1, "Burger", 50.0, "Food", stock=100)
        self.soda = Product(2, "Soda", 20.0, "Drink", stock=100)
        self.inv.add_product(self.burger, 10)
        self.inv.add_product(self.soda, 3)

        self.cust = Customer(1, "Ahmad", "0912", "a@ex.com", "Mashhad")
        self.order = Order(101, self.cust)
        self.order.add_product(self.burger, 2)
        self.order.add_product(self.soda, 1)

        self.reports = InventoryReports(self.inv, orders=[self.order])

    def test_inventory_summary(self):
        summary = self.reports.generate_inventory_summary()
        self.assertEqual(summary["total_products"], 2)
        self.assertGreater(summary["total_value"], 0)

    def test_low_stock_products(self):
        low = self.reports.low_stock_products(threshold=5)
        names = [p["name"] for p in low]
        self.assertIn("Soda", names)

    def test_category_stock_report(self):
        cats = self.reports.category_stock_report()
        self.assertIn("Food", cats)
        self.assertIn("Drink", cats)

    def test_top_consumed_products(self):
        top = self.reports.top_consumed_products(limit=2)
        names = [p["name"] for p in top]
        self.assertIn("Burger", names)

    def test_render_text_report(self):
        txt = self.reports.render_text_report()
        self.assertIn("Inventory Report", txt)
        self.assertIn("Low Stock Products:", txt)
        self.assertIn("Top Consumed Products:", txt)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInventoryReports)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestInventoryReports)
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
    root.title("Inventory Reports Test Results")

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
