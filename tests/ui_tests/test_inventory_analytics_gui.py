import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.inventory import Inventory
from analytics.inventory_analytics import InventoryAnalytics

class TestInventoryAnalytics(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.burger = Product(1, "Burger", 50.0, "Food", stock=100)
        self.soda = Product(2, "Soda", 20.0, "Drink", stock=100)
        self.inv.add_product(self.burger, 10)
        self.inv.add_product(self.soda, 1)

        self.cust = Customer(1, "Ahmad", "0912", "a@ex.com", "Mashhad")
        self.order = Order(101, self.cust)
        self.order.add_product(self.burger, 3)
        self.order.add_product(self.soda, 1)

        self.analytics = InventoryAnalytics(self.inv, orders=[self.order])

    def test_inventory_value_by_category(self):
        cats = self.analytics.inventory_value_by_category()
        self.assertIn("Food", cats)
        self.assertIn("Drink", cats)

    def test_fast_moving_products(self):
        fast = self.analytics.fast_moving_products(limit=2)
        names = [f["name"] for f in fast]
        self.assertIn("Burger", names)

    def test_slow_moving_products(self):
        slow = self.analytics.slow_moving_products(threshold=2)
        names = [s["name"] for s in slow]
        self.assertIn("Soda", names)

    def test_average_stock(self):
        avg = self.analytics.average_stock()
        self.assertGreater(avg, 0)

    def test_render_text_analysis(self):
        txt = self.analytics.render_text_analysis()
        self.assertIn("Inventory Analytics Report", txt)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInventoryAnalytics)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()
    expected_names = unittest.TestLoader().getTestCaseNames(TestInventoryAnalytics)
    status_map = {name: ("✅ Passed", "") for name in expected_names}
    for test, tb in result.failures: status_map[test.id().split(".")[-1]] = ("❌ Failed", tb)
    for test, tb in result.errors: status_map[test.id().split(".")[-1]] = ("⚠️ Error", tb)
    test_status = [(i+1, name, status_map[name][0], status_map[name][1]) for i, name in enumerate(expected_names)]
    total, failed, errors = result.testsRun, len(result.failures), len(result.errors)
    passed = total - failed - errors
    return test_status, total, passed, failed, errors, output_text

def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk(); root.title("Inventory Analytics Test Results")
    root.update_idletasks(); w,h=700,540; x=(root.winfo_screenwidth()//2)-(w//2); y=(root.winfo_screenheight()//2)-(h//2)
    root.geometry(f"{w}x{h}+{x}+{y}")
    tk.Label(root,text=f"Total:{total}|Passed:{passed}|Failed:{failed}|Errors:{errors}").pack(padx=10,pady=10,anchor="w")
    tree=ttk.Treeview(root,columns=("No","Test","Result"),show="headings",height=10)
    for col in ("No","Test","Result"): tree.heading(col,text=col)
    tree.column("No",width=50,anchor="center"); tree.column("Test",width=380,anchor="w"); tree.column("Result",width=160,anchor="center")
    for num,name,status,_ in test_status: tree.insert("", "end", values=(num,name,status))
    tree.pack(expand=True,fill="both",padx=10,pady=10)
    tk.Label(root,text="Console-like output").pack(padx=10,pady=(10,0),anchor="w")
    box=tk.Text(root,height=14,wrap="word"); box.insert("1.0",output_text); box.configure(state="disabled"); box.pack(expand=True,fill="both",padx=10,pady=(0,10))
    tk.Label(root,text=f"Summary→Total:{total},Passed:{passed},Failed:{failed},Errors:{errors}").pack(padx=10,pady=10,anchor="w")
    root.mainloop()

if __name__=="__main__": show_results_gui()
