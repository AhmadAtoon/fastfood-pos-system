import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer
from models.product import Product
from models.order import Order

class TestOrderModel(unittest.TestCase):
    def setUp(self):
        self.customer = Customer(1, "Ahmad", "0912000000", "ahmad@example.com", "Mashhad, Iran")
        self.product1 = Product(1, "Burger", 50.0, "Food", stock=10)
        self.product2 = Product(2, "Pizza", 80.0, "Food", stock=5)
        self.order = Order(1, self.customer)

    def test_add_product(self):
        self.order.add_product(self.product1, 2)
        self.assertEqual(len(self.order.products), 1)
        self.assertEqual(self.order.products[0]["quantity"], 2)

    def test_remove_product(self):
        self.order.add_product(self.product1, 2)
        self.order.remove_product(1)
        self.assertEqual(len(self.order.products), 0)

    def test_update_quantity(self):
        self.order.add_product(self.product1, 2)
        self.order.update_quantity(1, 5)
        self.assertEqual(self.order.products[0]["quantity"], 5)

    def test_calculate_total(self):
        self.order.add_product(self.product1, 2)
        self.order.add_product(self.product2, 1)
        self.order.set_delivery("Courier", 10.0)
        self.assertEqual(self.order.calculate_total(), 190.0)

    def test_apply_discount(self):
        self.order.add_product(self.product1, 2)
        self.order.apply_discount(10)
        self.assertEqual(self.order.products[0]["product"].price, 45.0)

    def test_update_status_valid(self):
        self.order.update_status("Paid")
        self.assertEqual(self.order.status, "Paid")

    def test_update_status_invalid(self):
        with self.assertRaises(ValueError):
            self.order.update_status("Unknown")

    def test_is_completed(self):
        self.order.update_status("Delivered")
        self.assertTrue(self.order.is_completed())

    def test_set_delivery(self):
        self.order.set_delivery("Courier", 15.0)
        self.assertEqual(self.order.delivery_method, "Courier")
        self.assertEqual(self.order.delivery_fee, 15.0)

    def test_get_delivery_info(self):
        self.order.set_delivery("Courier", 20.0)
        info = self.order.get_delivery_info()
        self.assertIn("Courier", info)
        self.assertIn("Mashhad", info)


def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestOrderModel)
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
    root.title("Order Model Test Results")

    # خلاصه کلی بالای پنجره
    summary = tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    summary.pack(padx=10, pady=10, anchor="w")

    # جدول تست‌ها با شماره‌گذاری
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=10)
    tree.heading("No", text="#")
    tree.heading("Test", text="Test Case")
    tree.heading("Result", text="Result")
    tree.column("No", width=40, anchor="center")
    tree.column("Test", width=240, anchor="w")
    tree.column("Result", width=120, anchor="center")

    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))

    tree.pack(expand=True, fill="both", padx=10, pady=10)

    # نمایش خروجی کنسول
    output_label = tk.Label(root, text="Console-like output")
    output_label.pack(padx=10, pady=(10, 0), anchor="w")

    output_box = tk.Text(root, height=12, wrap="word")
    output_box.insert("1.0", output_text)
    output_box.configure(state="disabled")
    output_box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    # خلاصه کلی پایین پنجره
    footer = tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}")
    footer.pack(padx=10, pady=10, anchor="w")

    root.mainloop()


if __name__ == "__main__":
    show_results_gui()
