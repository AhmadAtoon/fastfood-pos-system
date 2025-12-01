import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from datetime import datetime, timedelta
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.discount import Discount

class TestDiscountModel(unittest.TestCase):
    def setUp(self):
        self.customer = Customer(1, "Ahmad", "0912000000", "ahmad@example.com", "Tehran, Iran", membership_code="CUST-2025-0001")
        self.burger = Product(1, "Burger", 50.0, "Food", stock=10)
        self.drink = Product(2, "Soda", 20.0, "Drink", stock=50)
        self.order = Order(1, self.customer)
        self.order.add_product(self.burger, 2)  # 100
        self.order.add_product(self.drink, 3)   # 60
        self.order.set_delivery("Courier", 10.0)  # total pre-discount: 170

    def test_percentage_order_discount_valid(self):
        d = Discount(code="OFF10", kind="percentage", value=10, scope="order")
        amount, new_total = d.apply_to_order(self.order)
        self.assertEqual(amount, 16.0)       # 10% of 160 (without delivery)
        self.assertEqual(new_total, 154.0)   # (160 + 10) - 16

    def test_fixed_discount_cap(self):
        d = Discount(code="FIX50", kind="fixed", value=50, scope="order")
        amount, new_total = d.apply_to_order(self.order)
        self.assertEqual(amount, 50.0)
        self.assertEqual(new_total, 120.0)

    def test_category_discount(self):
        d = Discount(code="FOOD5", kind="percentage", value=5, scope="category", category="Food")
        amount, _ = d.apply_to_order(self.order)
        self.assertEqual(amount, 5.0)  # 5% of burgers total (100) = 5

    def test_product_discount(self):
        d = Discount(code="BURGER20", kind="fixed", value=20, scope="product", product_id=1)
        amount, _ = d.apply_to_order(self.order)
        self.assertEqual(amount, 20.0)  # capped to burger lines total (100)

    def test_min_total_and_membership(self):
        d = Discount(code="MEM15", kind="percentage", value=15, scope="order", min_order_total=100, requires_membership=True)
        self.assertTrue(d.is_valid(self.order))
        amount = d.calculate_discount(self.order)
        self.assertEqual(amount, 24.0)  # 15% of 160

    def test_date_window_validity(self):
        d = Discount(
            code="DAY10", kind="percentage", value=10, scope="order",
            start_at=datetime.now() - timedelta(days=1),
            end_at=datetime.now() + timedelta(days=1)
        )
        self.assertTrue(d.is_valid(self.order))

    def test_date_window_invalid(self):
        d = Discount(
            code="OLD10", kind="percentage", value=10, scope="order",
            start_at=datetime.now() - timedelta(days=3),
            end_at=datetime.now() - timedelta(days=1)
        )
        self.assertFalse(d.is_valid(self.order))

    def test_usage_limit(self):
        d = Discount(code="LIM10", kind="percentage", value=10, scope="order", usage_limit=1)
        amount, new_total = d.apply_to_order(self.order)
        self.assertGreater(amount, 0)
        d.consume()
        self.assertEqual(d.used_count, 1)
        self.assertFalse(d.is_valid(self.order))

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDiscountModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestDiscountModel)
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
    root.title("Discount Model Test Results")

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
