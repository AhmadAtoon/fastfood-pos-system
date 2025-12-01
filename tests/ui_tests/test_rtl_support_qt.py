# tests/ui_tests/test_rtl_support_qt.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTabWidget
from PyQt6.QtCore import QTimer, Qt
from i18n.rtl_support import (
    make_right_aligned_textedit,
    wrap_textedit_in_scroll,
    make_right_aligned_label,
    wrap_label_in_scroll,
)

def center_window(app, win):
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        frame = win.frameGeometry()
        frame.moveCenter(geo.center())
        win.move(frame.topLeft())

def show_comprehensive_rtl_test():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    win = QWidget()
    win.setWindowTitle("تست کامل راست‌چین - راه‌حل‌های مختلف")
    win.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    tab_widget = QTabWidget()
    tab_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    sample_text = (
        "این متن باید راست‌چین نمایش داده شود.\n"
        "خط دوم برای بررسی تراز راست.\n"
        "اعداد: ۱۲۳۴۵۶۷۸۹۰\n"
        "ترکیب فارسی و English و اعداد 12345 برای تست.\n"
        "پاراگراف طولانی برای تست پیچش کلمات و اطمینان از اینکه متن از سمت راست شروع می‌شود."
    )

    # تب 1: QTextEdit (پیشنهادی)
    tab1 = QWidget()
    tab1_layout = QVBoxLayout()
    title1 = QLabel('<div dir="rtl" style="text-align:center; font-size:18px; font-weight:bold; color: green;">✅ راه‌حل QTextEdit (پیشنهادی)</div>')
    title1.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tab1_layout.addWidget(title1)
    content1 = make_right_aligned_textedit(sample_text, font_family="Tahoma", point_size=12, bold=False)
    tab1_layout.addWidget(wrap_textedit_in_scroll(content1))
    tab1.setLayout(tab1_layout)
    tab_widget.addTab(tab1, "QTextEdit")

    # تب 2: QLabel + HTML
    tab2 = QWidget()
    tab2_layout = QVBoxLayout()
    title2 = QLabel('<div dir="rtl" style="text-align:center; font-size:18px; font-weight:bold; color: orange;">⚠️ راه‌حل QLabel با HTML</div>')
    title2.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tab2_layout.addWidget(title2)
    content2 = make_right_aligned_label(sample_text, font_family="Tahoma", point_size=12, bold=False)
    tab2_layout.addWidget(wrap_label_in_scroll(content2))
    tab2.setLayout(tab2_layout)
    tab_widget.addTab(tab2, "QLabel + HTML")

    # تب 3: QLabel ساده (برای مقایسه)
    tab3 = QWidget()
    tab3_layout = QVBoxLayout()
    title3 = QLabel('<div dir="rtl" style="text-align:center; font-size:18px; font-weight:bold; color: red;">❌ QLabel ساده (مشکل‌دار)</div>')
    title3.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tab3_layout.addWidget(title3)
    simple_label = QLabel(sample_text)
    simple_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    simple_label.setWordWrap(True)
    simple_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    simple_label.setStyleSheet("font-family: Tahoma; font-size: 12px; background-color: #fff0f0; padding: 8px;")
    tab3_layout.addWidget(wrap_label_in_scroll(simple_label))
    tab3.setLayout(tab3_layout)
    tab_widget.addTab(tab3, "QLabel ساده")

    main_layout = QVBoxLayout()
    main_title = QLabel('<div dir="rtl" style="text-align:center; font-size:24px; font-weight:bold; margin: 10px;">🧪 تست کامل پشتیبانی از راست‌چین (RTL)</div>')
    main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(main_title)
    description = QLabel('<div dir="rtl" style="text-align:center; font-size:14px; color: #666; margin: 5px;">برای مشاهده هر راه‌حل، تب مربوطه را انتخاب کنید</div>')
    description.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(description)
    main_layout.addWidget(tab_widget)
    win.setLayout(main_layout)

    win.resize(800, 500)
    win.show()
    QTimer.singleShot(50, lambda: center_window(app, win))
    sys.exit(app.exec())

if __name__ == "__main__":
    show_comprehensive_rtl_test()
