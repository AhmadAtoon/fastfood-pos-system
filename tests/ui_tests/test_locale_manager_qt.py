# tests/ui_tests/test_locale_manager_qt.py
import sys
from pathlib import Path

# افزودن مسیر ریشه پروژه به sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from i18n.locale_manager import LocaleManager
from i18n import rtl_support
from ui.font_manager import get_font

def center_window(app, win):
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        frame = win.frameGeometry()
        frame.moveCenter(geo.center())
        win.move(frame.topLeft())

def show_locale_demo():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    lm = LocaleManager(base_dir="locales", default_lang="fa")

    win = QWidget()
    win.setWindowTitle("تست Locale Manager")
    win.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    layout = QVBoxLayout()

    # عنوان از locale
    title_text = lm.get("app_title", fallback="سامانه فروش")
    title_label = QLabel()
    title_label.setFont(get_font(size=20, bold=True))
    rtl_support.set_html_rtl_label(title_label, title_text, align="center", size_px=20, bold=True)
    layout.addWidget(title_label)

    # دکمه‌ها از locale
    ok_btn = QPushButton(lm.get("ok_button", fallback="تأیید"))
    ok_btn.setFont(get_font(size=14))
    cancel_btn = QPushButton(lm.get("cancel_button", fallback="انصراف"))
    cancel_btn.setFont(get_font(size=14))

    layout.addWidget(ok_btn)
    layout.addWidget(cancel_btn)

    win.setLayout(layout)
    win.resize(420, 240)
    win.show()
    QTimer.singleShot(50, lambda: center_window(app, win))
    sys.exit(app.exec())

if __name__ == "__main__":
    show_locale_demo()
