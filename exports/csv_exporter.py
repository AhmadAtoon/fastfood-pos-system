import csv
from typing import List, Dict

class CSVExporter:
    def __init__(self, filename: str):
        self.filename = filename

    def export(self, data: List[Dict[str, any]]) -> str:
        """
        داده‌ها را به فایل CSV خروجی می‌گیرد.
        data: لیست دیکشنری‌ها با کلیدهای یکسان
        """
        if not data:
            raise ValueError("No data to export")

        keys = data[0].keys()
        with open(self.filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        return self.filename
