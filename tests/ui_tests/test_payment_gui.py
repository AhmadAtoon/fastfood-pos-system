import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.payment import Payment

class TestPaymentModel(unittest.TestCase):
    def setUp(self):
        self.customer = Customer(1, "Ahmad", "0912000000", "ahmad@example.com", "Mashhad, Iran")
        self.product = Product(1, "Burger", 50.0, "Food", stock=10)
        self.order = Order(1, self.customer)
        self.order.add_product(self.product, 2)            # 100
        self.order.set_delivery("Courier", 10.0)           # total: 110
        self.payment = Payment(1, self.order, self.order.calculate_total(), "Card")

    def test_process_payment_success(self):
        self.payment.process_payment(True, "TX-123")
        self.assertEqual(self.payment.status, "Completed")
        self.assertIsNotNone(self.payment.paid_at)

    def test_process_payment_fail(self):
        p = Payment(2, self.order, amount=110.0, method="Cash")
        p.process_payment(False)
        self.assertEqual(p.status, "Failed")

    def test_process_payment_positive_amount_required(self):
        p = Payment(3, self.order, amount=0.0, method="Cash")
        with self.assertRaises(ValueError):
            p.process_payment(True)

    def test_refund_valid(self):
        self.payment.process_payment(True)
        self.payment.refund()
        self.assertEqual(self.payment.status, "Refunded")

    def test_refund_invalid(self):
        p = Payment(4, self.order, amount=110.0, method="Online")
        with self.assertRaises(ValueError):
            p.refund()

    def test_update_status_valid(self):
        self.payment.update_status("Pending")
        self.assertEqual(self.payment.status, "Pending")

    def test_update_status_invalid(self):
        with self.assertRaises(ValueError):
            self.payment.update_status("Unknown")

    def test_get_payment_info(self):
        info = self.payment.get_payment_info()
        self.assertIn("Payment ID", info)
        self.assertIn("Method", info)

    def test_generate_invoice_preview(self):
        self.payment.process_payment(True, "TX-999")
        preview = self.payment.generate_invoice_preview()
        self.assertIn("Invoice Preview", preview)
        self.assertIn("Burger", preview)
        self.assertIn("Paid Amount", preview)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPaymentModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestPaymentModel)
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
    root.title("Payment Model Test Results")

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
