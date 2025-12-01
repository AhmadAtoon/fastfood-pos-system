import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from datetime import datetime, timedelta

from models.customer import Customer
from models.product import Product
from models.order import Order
from models.payment import Payment
from models.discount import Discount
from reports.sales_reports import SalesReports

class TestSalesReports(unittest.TestCase):
    def setUp(self):
        # داده‌های نمونه
        self.c1 = Customer(1, "Ahmad", "0912", "a@ex.com", "Mashhad", membership_code="M-001")
        self.c2 = Customer(2, "Sara", "0935", "s@ex.com", "Tehran")

        self.p_burger = Product(1, "Burger", 50.0, "Food", stock=100)
        self.p_soda = Product(2, "Soda", 20.0, "Drink", stock=100)

        # Order 1
        self.o1 = Order(101, self.c1)
        self.o1.add_product(self.p_burger, 2)  # 100
        self.o1.add_product(self.p_soda, 3)    # 60
        self.o1.set_delivery("Courier", 10.0)  # total 170
        self.o1.created_at = datetime.now() - timedelta(hours=3)

        # Discount for order 1
        self.d1 = Discount(code="OFF10", kind="percentage", value=10, scope="order")
        disc1, new_total1 = self.d1.apply_to_order(self.o1)  # 16, 154
        self.o1.discount_amount = disc1

        # Payment 1
        self.p1 = Payment(201, self.o1, amount=new_total1, method="Card")
        self.p1.process_payment(True, "TX-1")

        # Order 2
        self.o2 = Order(102, self.c2)
        self.o2.add_product(self.p_burger, 1)  # 50
        self.o2.set_delivery("Pickup", 0.0)    # total 50
        self.o2.created_at = datetime.now() - timedelta(hours=1)

        # Payment 2
        self.p2 = Payment(202, self.o2, amount=self.o2.calculate_total(), method="Cash")
        self.p2.process_payment(True, "TX-2")

        # Reports object
        self.reports = SalesReports(orders=[self.o1, self.o2], payments=[self.p1, self.p2], discounts=[self.d1])

    def test_sales_summary(self):
        summary = self.reports.generate_sales_summary()
        self.assertEqual(summary["total_orders"], 2)
        self.assertEqual(summary["completed_payments"], 2)
        self.assertEqual(summary["total_revenue"], 154.0 + 50.0)
        self.assertEqual(summary["total_discount"], 16.0)

    def test_top_products(self):
        top = self.reports.top_products(limit=2)
        names = [t["name"] for t in top]
        self.assertIn("Burger", names)
        self.assertIn("Soda", names)

    def test_top_customers(self):
        topc = self.reports.top_customers(limit=2)
        names = [t["name"] for t in topc]
        self.assertIn("Ahmad", names)
        self.assertIn("Sara", names)

    def test_render_text_report(self):
        txt = self.reports.render_text_report()
        self.assertIn("Sales Report", txt)
        self.assertIn("Top Products:", txt)
        self.assertIn("Top Customers:", txt)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSalesReports)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestSalesReports)
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
    root.title("Sales Reports Test Results")

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
