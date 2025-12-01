import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.payment import Payment
from analytics.customer_analytics import CustomerAnalytics

class TestCustomerAnalytics(unittest.TestCase):
    def setUp(self):
        # نمونه داده‌ها
        self.c1 = Customer(1, "Ahmad", "0912", "a@ex.com", "Mashhad")
        self.c2 = Customer(2, "Sara", "0935", "s@ex.com", "Tehran")

        self.p_burger = Product(1, "Burger", 50.0, "Food", stock=100)
        self.p_soda = Product(2, "Soda", 20.0, "Drink", stock=100)

        # سفارش 1
        self.o1 = Order(101, self.c1)
        self.o1.add_product(self.p_burger, 2)  # 100
        self.o1.add_product(self.p_soda, 1)    # 20
        # پرداخت 1
        self.p1 = Payment(201, self.o1, amount=self.o1.calculate_total(), method="Card")
        self.p1.process_payment(True, "TX-1")

        # سفارش 2
        self.o2 = Order(102, self.c2)
        self.o2.add_product(self.p_soda, 5)    # 100
        # پرداخت 2
        self.p2 = Payment(202, self.o2, amount=self.o2.calculate_total(), method="Cash")
        self.p2.process_payment(True, "TX-2")

        self.analytics = CustomerAnalytics(
            customers=[self.c1, self.c2],
            orders=[self.o1, self.o2],
            payments=[self.p1, self.p2]
        )

    def test_customer_lifetime_value(self):
        values = self.analytics.customer_lifetime_value()
        self.assertIn("Ahmad", values)
        self.assertIn("Sara", values)
        self.assertGreater(values["Ahmad"], 0)
        self.assertGreater(values["Sara"], 0)

    def test_loyal_customers(self):
        loyal = self.analytics.loyal_customers(limit=2)
        names = [l["name"] for l in loyal]
        self.assertIn("Ahmad", names)
        self.assertIn("Sara", names)

    def test_average_purchase_per_customer(self):
        avg = self.analytics.average_purchase_per_customer()
        self.assertGreater(avg, 0)

    def test_customer_distribution(self):
        dist = self.analytics.customer_distribution()
        self.assertIn("Mashhad", dist)
        self.assertIn("Tehran", dist)
        self.assertEqual(dist["Mashhad"], 1)
        self.assertEqual(dist["Tehran"], 1)

    def test_render_text_analysis(self):
        txt = self.analytics.render_text_analysis()
        self.assertIn("Customer Analytics Report", txt)
        self.assertIn("Loyal Customers:", txt)
        self.assertIn("Customer Distribution:", txt)

# -------------------------------
# اجرای تست‌ها و جمع‌آوری نتایج
# -------------------------------
def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomerAnalytics)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestCustomerAnalytics)
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

# -------------------------------
# نمایش گرافیکی نتایج (پنجره وسط صفحه)
# -------------------------------
def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk()
    root.title("Customer Analytics Test Results")

    # پنجره در وسط صفحه باز شود
    root.update_idletasks()
    w, h = 700, 540
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    summary = tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    summary.pack(padx=10, pady=10, anchor="w")

    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=10)
    tree.heading("No", text="#")
    tree.heading("Test", text="Test Case")
    tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center")
    tree.column("Test", width=380, anchor="w")
    tree.column("Result", width=160, anchor="center")

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
