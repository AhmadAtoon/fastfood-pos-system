import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.payment import Payment
from models.discount import Discount
from reports.financial_reports import FinancialReports

class TestFinancialReports(unittest.TestCase):
    def setUp(self):
        self.c1 = Customer(1, "Ahmad", "0912", "a@ex.com", "Mashhad")
        self.c2 = Customer(2, "Sara", "0935", "s@ex.com", "Tehran")

        self.p_burger = Product(1, "Burger", 50.0, "Food", stock=100)
        self.p_soda = Product(2, "Soda", 20.0, "Drink", stock=100)

        # Order 1 با تخفیف
        self.o1 = Order(101, self.c1)
        self.o1.add_product(self.p_burger, 2)  # 100
        self.o1.set_delivery("Courier", 10.0)  # 110
        self.d1 = Discount("OFF10", "percentage", 10, "order")
        disc1, new_total1 = self.d1.apply_to_order(self.o1)
        self.o1.discount_amount = disc1
        self.p1 = Payment(201, self.o1, amount=new_total1, method="Card")
        self.p1.process_payment(True, "TX-1")

        # Order 2 بدون تخفیف
        self.o2 = Order(102, self.c2)
        self.o2.add_product(self.p_soda, 5)  # 100
        self.o2.set_delivery("Pickup", 0.0)
        self.p2 = Payment(202, self.o2, amount=self.o2.calculate_total(), method="Cash")
        self.p2.process_payment(True, "TX-2")

        self.reports = FinancialReports(orders=[self.o1, self.o2], payments=[self.p1, self.p2])

    def test_financial_summary(self):
        summary = self.reports.generate_financial_summary()
        self.assertEqual(summary["total_orders"], 2)
        self.assertEqual(summary["completed_payments"], 2)

    def test_discount_summary(self):
        discounts = self.reports.discount_summary()
        self.assertGreater(discounts["total_discount"], 0)

    def test_net_revenue(self):
        net = self.reports.net_revenue()
        self.assertGreater(net, 0)

    def test_render_text_report(self):
        txt = self.reports.render_text_report()
        self.assertIn("Financial Report", txt)
        self.assertIn("Net Revenue", txt)

# -------------------------------
# اجرای تست‌ها و نمایش گرافیکی
# -------------------------------
def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFinancialReports)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestFinancialReports)
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
    root.title("Financial Reports Test Results")

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
