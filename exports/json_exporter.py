import json
from typing import List, Dict, Any

class JSONExporter:
    def __init__(self, filename: str):
        self.filename = filename

    def export(self, data: List[Dict[str, Any]]) -> str:
        """
        داده‌ها را به فایل JSON خروجی می‌گیرد.
        data: لیست دیکشنری‌ها یا هر ساختار قابل سریال‌سازی
        """
        if not data:
            raise ValueError("No data to export")

        with open(self.filename, mode="w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return self.filename

    def export_single(self, record: Dict[str, Any]) -> str:
        """
        یک رکورد منفرد را به JSON ذخیره می‌کند.
        """
        with open(self.filename, mode="w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=4)
        return self.filename

    def export_pretty(self, data: List[Dict[str, Any]]) -> str:
        """
        داده‌ها را با فرمت زیبا (pretty print) خروجی می‌دهد.
        """
        with open(self.filename, mode="w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return self.filename
