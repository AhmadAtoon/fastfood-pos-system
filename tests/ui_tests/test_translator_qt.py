# tests/ui_tests/test_translator_qt.py
import sys
import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextBrowser, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer
from i18n import translator
from ui.font_manager import get_font

def center_window(app: QApplication, win: QWidget):
    """قرار دادن پنجره در مرکز صفحه (استاندارد پروژه)."""
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        frame = win.frameGeometry()
        frame.moveCenter(geo.center())
        win.move(frame.topLeft())

def show_translator_demo():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    win = QWidget()
    win.setWindowTitle("نمایش تاریخ فارسی RTL")
    win.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    root = QVBoxLayout()

    # عنوان وسط‌چین
    title = QLabel("سامانه فروش فست‌فود")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setFont(get_font(size=22, bold=True))
    root.addWidget(title)

    # متن محتوا راست‌چین
    content = QTextBrowser()
    content.setAlignment(Qt.AlignmentFlag.AlignRight)
    content.setFont(get_font(size=14))

    today_line = translator.format_date(datetime.datetime.now(), calendar="jalali")
    body = f"تاریخ امروز: {today_line}\nاین یک متن نمونه برای تست راست‌چین است."
    content.setPlainText(body)
    root.addWidget(content)

    # ردیف: دکمه در راست، متن بعد از آن
    row = QHBoxLayout()
    btn = QPushButton("🔔")
    btn.setFont(get_font(size=14))
    lbl = QLabel("اعلان جدید")
    lbl.setFont(get_font(size=14))
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

    row.addWidget(btn)
    row.addWidget(lbl)
    row.addStretch(1)
    root.addLayout(row)

    win.setLayout(root)
    win.resize(720, 440)
    win.show()

    # مرکز کردن بعد از show
    QTimer.singleShot(50, lambda: center_window(app, win))
    sys.exit(app.exec())

if __name__ == "__main__":
    show_translator_demo()
