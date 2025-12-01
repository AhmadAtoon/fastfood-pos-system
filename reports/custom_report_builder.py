from typing import Callable, Dict, List

class CustomReportBuilder:
    def __init__(self):
        self.sections: Dict[str, Callable[[], str]] = {}

    def add_section(self, name: str, generator_func: Callable[[], str]) -> None:
        """
        افزودن یک بخش گزارش با نام و تابع تولیدکننده
        """
        self.sections[name] = generator_func

    def build_report(self) -> Dict[str, str]:
        """
        اجرای همه بخش‌ها و برگرداندن خروجی به صورت دیکشنری
        """
        report: Dict[str, str] = {}
        for name, func in self.sections.items():
            try:
                report[name] = func()
            except Exception as e:
                report[name] = f"Error generating section {name}: {e}"
        return report

    def render_text_report(self) -> str:
        """
        خروجی متنی ترکیبی
        """
        report = self.build_report()
        lines: List[str] = []
        lines.append("Custom Report")
        lines.append("=" * 40)
        for name, content in report.items():
            lines.append(f"[{name}]")
            lines.append(content)
            lines.append("-" * 40)
        return "\n".join(lines)

    def save_to_file(self, path: str) -> None:
        """
        ذخیره گزارش در فایل متنی
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render_text_report())
