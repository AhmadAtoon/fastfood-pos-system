from typing import List, Dict, Any
from fpdf import FPDF

class PDFExporter:
    def __init__(self, filename: str):
        self.filename = filename

    def export(self, data: List[Dict[str, Any]], title: str = "Report") -> str:
        """
        داده‌ها را به فایل PDF خروجی می‌گیرد.
        data: لیست دیکشنری‌ها با کلیدهای یکسان
        title: عنوان گزارش
        """
        if not data:
            raise ValueError("No data to export")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, title, ln=True, align="C")

        # هدرها
        pdf.set_font("Arial", "B", 12)
        headers = list(data[0].keys())
        for h in headers:
            pdf.cell(40, 10, h, 1, 0, "C")
        pdf.ln()

        # داده‌ها
        pdf.set_font("Arial", "", 12)
        for row in data:
            for h in headers:
                pdf.cell(40, 10, str(row.get(h, "")), 1, 0, "C")
            pdf.ln()

        pdf.output(self.filename)
        return self.filename

    def export_summary(self, summary: str, title: str = "Summary") -> str:
        """
        خروجی یک متن خلاصه به PDF
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, title, ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, summary)
        pdf.output(self.filename)
        return self.filename
