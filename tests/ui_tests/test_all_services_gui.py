# tests/ui_tests/test_all_services_gui.py
import tkinter as tk
from tkinter import ttk
from io import StringIO
import json
import os
import time

# وارد کردن توابع جمع‌آوری نتایج از هر ماژول تستی که قبلاً ساخته‌ایم
from tests.ui_tests.test_auth_decorators_gui import run_suite_and_collect as run_auth_decorators
from tests.ui_tests.test_inventory_permissions_gui import run_suite_and_collect as run_inventory
from tests.ui_tests.test_print_permissions_gui import run_suite_and_collect as run_print
from tests.ui_tests.test_template_service_gui import run_suite_and_collect as run_template
from tests.ui_tests.test_reporting_service_gui import run_suite_and_collect as run_reporting
from tests.ui_tests.test_notification_service_gui import run_suite_and_collect as run_notification
from tests.ui_tests.test_analytics_service_gui import run_suite_and_collect as run_analytics
from tests.ui_tests.test_order_service_gui import run_suite_and_collect as run_order
from tests.ui_tests.test_payment_service_gui import run_suite_and_collect as run_payment

MODULES = [
    ("Auth Decorators", run_auth_decorators),
    ("Inventory Service", run_inventory),
    ("Print Service", run_print),
    ("Template Service", run_template),
    ("Reporting Service", run_reporting),
    ("Notification Service", run_notification),
    ("Analytics Service", run_analytics),
    ("Order Service", run_order),
    ("Payment Service (experimental)", run_payment),
]

SUMMARY_DIR = os.path.join(os.getcwd(), "test_reports")
os.makedirs(SUMMARY_DIR, exist_ok=True)
SUMMARY_FILE = os.path.join(SUMMARY_DIR, "summary.json")

def run_all():
    aggregated = []
    total = passed = failed = errors = 0
    combined_output = []
    for name, runner in MODULES:
        test_status, t, p, f, e, out = runner()
        aggregated.append({
            "module": name,
            "total": t,
            "passed": p,
            "failed": f,
            "errors": e,
            "details": [{"no": s[0], "case": s[1], "result": s[2]} for s in test_status],
            "console": out
        })
        total += t; passed += p; failed += f; errors += e
        combined_output.append(f"=== {name} ===\n{out}\n")
    # ذخیرهٔ خلاصهٔ JSON (در صورت وجود بازنویسی می‌شود)
    summary = {
        "generated_at": int(time.time()),
        "total_modules": len(MODULES),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "modules": aggregated
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    return summary, "\n\n".join(combined_output)

def show_gui():
    summary, combined_output = run_all()
    root = tk.Tk()
    root.title("All Services Test Results")
    w, h = 900, 700
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    header = f"Modules: {summary['total_modules']} | Tests: {summary['total_tests']} | Passed: {summary['passed']} | Failed: {summary['failed']} | Errors: {summary['errors']}"
    tk.Label(root, text=header).pack(padx=10, pady=8, anchor="w")

    cols = ("No", "Module", "Total", "Passed", "Failed", "Errors")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c)
    tree.column("No", width=40, anchor="center")
    tree.column("Module", width=360, anchor="w")
    tree.column("Total", width=60, anchor="center")
    tree.column("Passed", width=60, anchor="center")
    tree.column("Failed", width=60, anchor="center")
    tree.column("Errors", width=60, anchor="center")

    for i, m in enumerate(summary["modules"], start=1):
        tree.insert("", "end", values=(i, m["module"], m["total"], m["passed"], m["failed"], m["errors"]))
    tree.pack(fill="x", padx=10, pady=6)

    tk.Label(root, text="Combined console output").pack(padx=10, pady=(6,0), anchor="w")
    box = tk.Text(root, height=22, wrap="word")
    box.insert("1.0", combined_output)
    box.configure(state="disabled")
    box.pack(expand=True, fill="both", padx=10, pady=(0,10))

    tk.Label(root, text=f"Summary saved to: {SUMMARY_FILE}").pack(padx=10, pady=(0,10), anchor="w")
    root.mainloop()

if __name__ == "__main__":
    show_gui()
