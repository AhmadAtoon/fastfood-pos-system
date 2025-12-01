# i18n/rtl_support.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QScrollArea, QTextEdit
from PyQt6.QtGui import QFont, QTextOption

def make_right_aligned_textedit(text: str, font_family: str = "Tahoma", point_size: int = 14, bold: bool = False) -> QTextEdit:
    """
    نسخهٔ ساده و پایدار: QTextEdit راست‌چین که قبلاً کار می‌کرد.
    """
    te = QTextEdit()
    te.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    # تنظیم فونت ساده (بدون بررسی پیچیده)
    font = QFont(font_family, point_size)
    font.setBold(bold)
    te.setFont(font)

    # خط‌شکنی و پیچش کلمات
    te.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    try:
        te.setWordWrapMode(QTextOption.WrapMode.WordWrap)
    except Exception:
        pass

    # تراز کلی و قرار دادن متن
    te.setAlignment(Qt.AlignmentFlag.AlignRight)
    te.setPlainText("" if text is None else str(text))
    te.setReadOnly(True)

    # استایل ساده برای ظاهر
    te.setStyleSheet("""
        QTextEdit {
            background-color: white;
            border: 1px solid #cccccc;
            padding: 8px;
        }
    """)
    return te

def wrap_textedit_in_scroll(text_edit: QTextEdit) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(text_edit)
    sa.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    return sa

def make_right_aligned_label(text: str, font_family: str = "Tahoma", point_size: int = 14, bold: bool = False) -> QLabel:
    lbl = QLabel()
    lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    lbl.setWordWrap(True)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
    font = lbl.font()
    font.setFamily(font_family)
    font.setPointSize(point_size)
    font.setBold(bold)
    lbl.setFont(font)
    safe = "" if text is None else str(text).replace("\n", "<br>")
    lbl.setText(f'<div dir="rtl" style="text-align:right;">{safe}</div>')
    return lbl

def wrap_label_in_scroll(label: QLabel) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(label)
    sa.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    return sa
