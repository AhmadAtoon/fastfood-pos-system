import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
import os
import json
from exports.json_exporter import JSONExporter

class TestJSONExporter(unittest.TestCase):
    def setUp(self):
        self.filename = "test_output.json"
        self.data = [
            {"Date": "2025-11-25", "Product": "Burger", "Qty": 3, "Amount": 150},
            {"Date": "2025-11-26", "Product": "Soda", "Qty": 2, "Amount": 40},
        ]
        self.exporter = JSONExporter(self.filename)

    def test_export_creates_file(self):
        path = self.exporter.export(self.data)
        self.assertTrue(os.path.exists(path))

    def test_export_has_keys(self):
        self.exporter.export(self.data)
        with open(self.filename, encoding="utf-8") as f:
            content = json.load(f)
        self.assertIn("Date", content[0])
        self.assertIn("Product", content[0])

    def test_export_single(self):
        record = {"Customer": "Ahmad", "City": "Shiraz"}
        path = self.exporter.export_single(record)
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content["Customer"], "Ahmad")

    def test_export_pretty(self):
        path = self.exporter.export_pretty(self.data)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("\n", text)  # pretty print has newlines

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJSONExporter)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()
    expected_names = unittest.TestLoader().getTestCaseNames(TestJSONExporter)
    status_map = {name: ("✅ Passed", "") for name in expected_names}
    for test, tb in result.failures:
        status_map[test.id().split(".")[-1]] = ("❌ Failed", tb)
    for test, tb in result.errors:
        status_map[test.id().split(".")[-1]] = ("⚠️ Error", tb)
    test_status = [(i+1, name, status_map[name][0], status_map[name][1]) for i, name in enumerate(expected_names)]
    total = result.testsRun; failed = len(result.failures); errors = len(result.errors)
    passed = total - failed - errors
    return test_status, total, passed, failed, errors, output_text

def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk(); root.title("JSON Exporter Test Results")
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
