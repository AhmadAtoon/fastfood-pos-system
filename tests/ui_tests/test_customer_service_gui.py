import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from services.customer_service import CustomerService

class TestCustomerService(unittest.TestCase):
    def setUp(self):
        self.srv = CustomerService()
        # ایجاد چند مشتری نمونه
        self.c1 = self.srv.create_customer({"name": "Ahmad", "phone": "09120000001", "email": "ahmad@example.com"})
        self.c2 = self.srv.create_customer({"name": "Sara", "phone": "09120000002", "email": "sara@example.com"})
        self.srv.add_address(self.c1["customer_id"], {"label": "Home", "line1": "Street 1", "city": "Shiraz", "postal_code": "713xx"})

    def test_create_and_get(self):
        c = self.srv.get_customer(self.c1["customer_id"])
        self.assertIsNotNone(c)
        self.assertEqual(c["name"], "Ahmad")

    def test_update_and_list(self):
        self.srv.update_customer(self.c2["customer_id"], {"name": "Sara A"})
        lst = self.srv.list_customers({"name_contains": "sara"})
        self.assertTrue(any(x["customer_id"] == self.c2["customer_id"] for x in lst))

    def test_find_by_phone(self):
        found = self.srv.find_by_phone("09120000001")
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Ahmad")

    def test_address_management(self):
        addrs = self.srv.get_customer(self.c1["customer_id"])["addresses"]
        self.assertGreaterEqual(len(addrs), 1)
        addr = addrs[0]
        removed = self.srv.remove_address(self.c1["customer_id"], addr["address_id"])
        self.assertTrue(removed)

    def test_delete_customer(self):
        ok = self.srv.delete_customer(self.c2["customer_id"])
        self.assertTrue(ok)
        self.assertIsNone(self.srv.get_customer(self.c2["customer_id"]))

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomerService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestCustomerService)
    status_map = {name: ("✅ Passed", "") for name in expected}
    for test, tb in result.failures:
        status_map[test.id().split(".")[-1]] = ("❌ Failed", tb)
    for test, tb in result.errors:
        status_map[test.id().split(".")[-1]] = ("⚠️ Error", tb)

    test_status = [(i+1, name, status_map[name][0], status_map[name][1]) for i, name in enumerate(expected)]
    total = result.testsRun; failed = len(result.failures); errors = len(result.errors)
    passed = total - failed - errors
    return test_status, total, passed, failed, errors, output_text

def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk()
    root.title("Customer Service Test Results")
    root.update_idletasks()
    w, h = 760, 520
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=8)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=480, anchor="w"); tree.column("Result", width=160, anchor="center")
    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    tk.Label(root, text="Console-like output").pack(padx=10, pady=(10, 0), anchor="w")
    box = tk.Text(root, height=10, wrap="word")
    box.insert("1.0", output_text); box.configure(state="disabled")
    box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    root.mainloop()

if __name__ == "__main__":
    show_results_gui()
