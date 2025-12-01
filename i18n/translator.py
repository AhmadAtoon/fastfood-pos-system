# i18n/translator.py
from datetime import datetime

try:
    import jdatetime
except Exception:
    jdatetime = None

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

def to_fa_digits(text: str) -> str:
    """تبدیل اعداد لاتین به فارسی."""
    s = str(text)
    return "".join(FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in s)

def format_date(dt: datetime, calendar: str = "jalali") -> str:
    """
    تاریخ شمسی یا میلادی با فرمت استاندارد YYYY/MM/DD و اعداد فارسی.
    مثال خروجی: ۱۴۰۴/۰۹/۰۹
    """
    if calendar == "jalali" and jdatetime is not None:
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        formatted = jd.strftime("%Y/%m/%d")
        return to_fa_digits(formatted)
    # fallback میلادی
    formatted = dt.strftime("%Y/%m/%d")
    return to_fa_digits(formatted)
