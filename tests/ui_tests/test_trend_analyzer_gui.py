import unittest
import tkinter as tk
from tkinter import ttk
from io import StringIO
from analytics.trend_analyzer import TrendAnalyzer

class TestTrendAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data = {"2025-11-25": 100, "2025-11-26": 120, "2025-11-27": 90}
        self.analyzer = TrendAnalyzer(self.data)

    def test_average_value(self):
        avg = self.analyzer.average_value()
        self.assertGreater(avg, 0)

    def test_trend_direction(self):
        trend = self.analyzer.trend_direction()
        self.assertIn(trend, ["Upward","Downward","Stable","No trend"])

    def test_max_value(self):
        self.assertEqual(self.analyzer.max_value(), 120)

    def test_min_value(self):
        self.assertEqual(self.analyzer.min_value(), 90)

    def test_render_text_analysis(self):
        txt = self.analyzer.render_text_analysis()
        self.assertIn("Trend Analysis Report", txt)

def run_suite_and_collect():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrendAnalyzer)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    output_text = stream.getvalue()
    expected_names = unittest.TestLoader().getTestCaseNames(TestTrendAnalyzer)
    status_map = {name: ("✅ Passed", "") for name in expected_names}
    for test, tb in result.failures: status_map[test.id().split(".")[-1]] = ("❌ Failed", tb)
    for test, tb in result.errors: status_map[test.id().split(".")[-1]] = ("⚠️ Error", tb)
    test_status = [(i+1, name, status_map[name][0], status_map[name][1]) for i, name in enumerate(expected_names)]
    total, failed, errors = result.testsRun, len(result.failures), len(result.errors)
    passed = total - failed - errors
    return test_status, total, passed, failed, errors, output_text

def show_results_gui():
    test_status, total, passed, failed, errors, output_text = run_suite_and_collect()
    root = tk.Tk(); root.title("Trend Analyzer Test Results")
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
