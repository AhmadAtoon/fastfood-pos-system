import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer

class TestCustomerModel(unittest.TestCase):
    def setUp(self):
        self.customer = Customer(
            1,
            "Ahmad",
            "0912000000",
            "ahmad@example.com",
            "Mashhad, Iran"
        )

    # --- تست اطلاعات پایه ---
    def test_update_name_valid(self):
        self.customer.update_name("Ali")
        self.assertEqual(self.customer.name, "Ali")

    def test_update_address_valid(self):
        self.customer.update_address("Tehran, Iran")
        self.assertEqual(self.customer.address, "Tehran, Iran")

    # --- تست کد اشتراک ---
    def test_assign_membership_code(self):
        self.customer.assign_membership_code("CUST-2025-0001")
        self.assertTrue(self.customer.has_membership())
        self.assertEqual(self.customer.membership_code, "CUST-2025-0001")

    def test_assign_membership_code_invalid(self):
        with self.assertRaises(ValueError):
            self.customer.assign_membership_code("")

    # --- تست وفاداری ---
    def test_add_loyalty_points(self):
        self.customer.add_loyalty_points(200)
        self.assertEqual(self.customer.loyalty_points, 200)
        self.assertEqual(self.customer.get_loyalty_status(), "Silver")

    def test_redeem_loyalty_points_valid(self):
        self.customer.add_loyalty_points(300)
        self.customer.redeem_loyalty_points(100)
        self.assertEqual(self.customer.loyalty_points, 200)

    def test_redeem_loyalty_points_invalid(self):
        with self.assertRaises(ValueError):
            self.customer.redeem_loyalty_points(50)

    def test_loyalty_status_levels(self):
        self.customer.loyalty_points = 50
        self.assertEqual(self.customer.get_loyalty_status(), "Bronze")
        self.customer.loyalty_points = 150
        self.assertEqual(self.customer.get_loyalty_status(), "Silver")
        self.customer.loyalty_points = 600
        self.assertEqual(self.customer.get_loyalty_status(), "Gold")
        self.customer.loyalty_points = 1200
        self.assertEqual(self.customer.get_loyalty_status(), "Platinum")

    # --- تست وضعیت فعال ---
    def test_activation_cycle(self):
        self.customer.deactivate()
        self.assertFalse(self.customer.active)
        self.customer.activate()
        self.assertTrue(self.customer.active)


def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomerModel)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected_names = unittest.TestLoader().getTestCaseNames(TestCustomerModel)
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
    root.title("Customer Model Test Results")

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
