import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.payment import Payment
from models.discount import Discount
from models.invoice import Invoice

class TestInvoiceModel(unittest.TestCase):
    def setUp(self):
        self.customer = Customer(1, "Ahmad", "0912000000", "ahmad@example.com", "Tehran, Iran", membership_code="CUST-2025-0001")
        self.burger = Product(1, "Burger", 50.0, "Food", stock=10)
        self.drink = Product(2, "Soda", 20.0, "Drink", stock=50)
        self.order = Order(1, self.customer)
        self.order.add_product(self.burger, 2)  # 100
        self.order.add_product(self.drink, 3)   # 60
        self.order.set_delivery("Courier", 10.0)  # pre-discount total: 170

    def test_invoice_without_discount(self):
        payment = Payment(1, self.order, amount=self.order.calculate_total(), method="Card")
        payment.process_payment(True, "TX-INV-001")
        invoice = Invoice(1001, self.order, payment, discount_amount=0.0, store_name="Demo POS", store_address="Tehran")
        preview = invoice.render_text_preview()
        self.assertIn("Invoice #1001", preview)
        self.assertIn("TOTAL: 170.0", preview)

    def test_invoice_with_discount(self):
        d = Discount(code="OFF10", kind="percentage", value=10, scope="order")
        disc_amount, new_total = d.apply_to_order(self.order)  # 16.0 discount, new_total 154.0
        payment = Payment(2, self.order, amount=new_total, method="Cash")
        payment.process_payment(True, "TX-INV-002")
        invoice = Invoice(1002, self.order, payment, discount_amount=disc_amount, store_name="Demo POS", store_address="Tehran")
        data = invoice.generate_data()
        self.assertEqual(data["summary"]["discount"], 16.0)
        self.assertEqual(data["summary"]["total"], 154.0)
        preview = invoice.render_text_preview()
        self.assertIn("Discount: 16.0", preview)
        self.assertIn("TOTAL: 154.0", preview)

    def test_invoice_dict_integrity(self):
        payment = Payment(3, self.order, amount=self.order.calculate_total(), method="Online")
        payment.process_payment(True, "TX-INV-003")
        invoice = Invoice(1003, self.order, payment, discount_amount=0.0)
        d = invoice.to_dict()
        self.assertEqual(d["order"]["id"], 1)
        self.assertEqual(d["payment"]["status"], "Completed")
        self.assertGreater(len(d["lines"]), 0)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvoiceModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestInvoiceModel)
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
    root.title("Invoice Model Test Results")

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
