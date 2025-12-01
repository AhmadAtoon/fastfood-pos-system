# ui/font_manager.py
from PyQt6.QtGui import QFontDatabase, QFont

def get_font(family_candidates=("Tahoma", "Segoe UI", "Arial"), size=14, bold=False):
    """
    انتخاب فونت با اولویت Tahoma. اگر موجود نبود، از فونت پیش‌فرض سیستم استفاده می‌کند.
    """
    families = QFontDatabase.families()
    chosen = None
    for cand in family_candidates:
        if cand in families:
            chosen = cand
            break
    font = QFont(chosen if chosen else QFont().family(), size)
    font.setBold(bold)
    return font
