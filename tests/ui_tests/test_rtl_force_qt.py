# tests/ui_tests/test_rtl_force_qt.py
import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QTextBlockFormat, QTextOption, QFont

RLM = "\u200F"  # Right-to-Left mark

def force_rtl_insert(te: QTextEdit, text: str, point_size: int = 14, bold: bool = False):
    # widget + app direction
    te.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # font
    f = QFont("Tahoma", point_size)
    f.setBold(bold)
    te.setFont(f)

    # document default alignment
    doc = te.document()
    opt = doc.defaultTextOption()
    opt.setAlignment(Qt.AlignmentFlag.AlignRight)
    doc.setDefaultTextOption(opt)

    # clear and insert block-by-block, prefix each line with RLM
    te.clear()
    cursor = QTextCursor(doc)
    lines = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for i, line in enumerate(lines):
        cursor.movePosition(QTextCursor.MoveOperation.End)
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(Qt.AlignmentFlag.AlignRight)
        try:
            block_fmt.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        except Exception:
            pass
        cursor.insertBlock(block_fmt)
        # prefix with RLM to force RTL direction at start of block
        cursor.insertText(RLM + line)
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    te.setTextCursor(cursor)
    te.setReadOnly(True)

def center_window(app, win):
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        frame = win.frameGeometry()
        frame.moveCenter(geo.center())
        win.move(frame.topLeft())

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    win = QWidget()
    win.setWindowTitle("تست راست‌چین قطعی")
    win.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    layout = QVBoxLayout()

    title = QLabel('<div dir="rtl" style="text-align:center; font-size:20px; font-weight:bold;">این یک عنوان وسط‌چین است</div>')
    title.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    layout.addWidget(title)

    te = QTextEdit()
    sample = (
        "این متن باید راست‌چین نمایش داده شود.\n"
        "خط دوم برای بررسی تراز راست.\n"
        "اعداد: ۱۲۳۴۵۶۷۸۹۰\n"
        "ترکیب فارسی و English و اعداد 12345 برای تست.\n"
        "پاراگراف طولانی برای تست پیچش کلمات و اطمینان از اینکه متن از سمت راست شروع می‌شود."
    )
    force_rtl_insert(te, sample, point_size=14, bold=False)
    layout.addWidget(te)

    win.setLayout(layout)
    win.resize(760, 420)
    win.show()
    QTimer.singleShot(50, lambda: center_window(app, win))
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
