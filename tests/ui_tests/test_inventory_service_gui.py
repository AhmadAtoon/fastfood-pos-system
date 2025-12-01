import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from services.inventory_service import InventoryService

class TestInventoryService(unittest.TestCase):
    def setUp(self):
        self.srv = InventoryService()
        # افزودن آیتم‌ها
        self.srv.upsert_item("FOOD-001", "Burger", 100, 120000, {"category": "food"})
        self.srv.upsert_item("DRINK-002", "Soda", 150, 20000, {"category": "drink"})
        self.srv.upsert_item("SIDE-003", "Fries", 80, 50000, {"category": "side"})

    def test_upsert_and_get(self):
        it = self.srv.get_item("FOOD-001")
        self.assertIsNotNone(it)
        self.assertEqual(it["name"], "Burger")

    def test_list_filters(self):
        lst = self.srv.list_items({"name_contains": "o", "min_stock": 90})
        self.assertTrue(all(i["stock"] >= 90 for i in lst))

    def test_adjust_stock(self):
        tx = self.srv.adjust_stock("FOOD-001", -5, reason="waste")
        self.assertTrue(tx["final_stock"] <= 95)

    def test_reserve_release_commit(self):
        # رزرو
        res = self.srv.reserve_for_order("ORD-1001", [{"sku": "FOOD-001", "qty": 2}, {"sku": "DRINK-002", "qty": 3}])
        self.assertEqual(len(res["reserved"]), 2)
        # آزادسازی
        rel = self.srv.release_order("ORD-1001")
        self.assertEqual(len(rel["released"]), 2)
        # رزرو دوباره و تأیید
        res2 = self.srv.reserve_for_order("ORD-1002", [{"sku": "FOOD-001", "qty": 4}])
        self.assertEqual(len(res2["reserved"]), 1)
        com = self.srv.commit_order("ORD-1002")
        self.assertEqual(len(com["committed"]), 1)

    def test_transactions_history(self):
        self.srv.adjust_stock("SIDE-003", +10, "restock")
        self.srv.adjust_stock("SIDE-003", -2, "waste")
        txs = self.srv.transactions()
        self.assertGreaterEqual(len(txs), 2)


def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInventoryService)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()

    expected = unittest.TestLoader().getTestCaseNames(TestInventoryService)
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
    root.title("Inventory Service Test Results")

    # پنجره وسط صفحه
    root.update_idletasks()
    w, h = 780, 580
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text=f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}").pack(padx=10, pady=10, anchor="w")

    tree = ttk.Treeview(root, columns=("No", "Test", "Result"), show="headings", height=10)
    tree.heading("No", text="#"); tree.heading("Test", text="Test Case"); tree.heading("Result", text="Result")
    tree.column("No", width=50, anchor="center"); tree.column("Test", width=440, anchor="w"); tree.column("Result", width=180, anchor="center")
    for num, name, status, _ in test_status:
        tree.insert("", "end", values=(num, name, status))
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    tk.Label(root, text="Console-like output").pack(padx=10, pady=(10, 0), anchor="w")
    box = tk.Text(root, height=14, wrap="word")
    box.insert("1.0", output_text); box.configure(state="disabled")
    box.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    tk.Label(root, text=f"Summary → Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}").pack(padx=10, pady=10, anchor="w")
    root.mainloop()


if __name__ == "__main__":
    show_results_gui()
