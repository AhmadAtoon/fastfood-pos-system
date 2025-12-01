"""
style_builder.py - سیستم تولید استایل‌شیت از فایل‌های YAML
نسخه نهایی با رفع تمام خطاها
"""

import yaml
import os
import sys
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime

# اضافه کردن مسیر پروژه برای ایمپورت
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# مقادیر پیش‌فرض
DEFAULT_COLORS = {
    'primary': '#2E86AB',
    'primary_light': '#5DA8D1',
    'primary_dark': '#1C5E7A',
    'secondary': '#A23B72',
    'secondary_light': '#D46BA0',
    'secondary_dark': '#7A2854',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'background': '#FFFFFF',
    'text_primary': '#212529',
    'border': '#6C757D'
}

DEFAULT_TYPOGRAPHY = {
    'font_primary': 'B Nazanin',
    'font_size_normal': 14,
    'font_size_large': 16,
    'font_size_small': 12,
    'body': 14,
    'h1': 24,
    'h2': 20
}

DEFAULT_SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '24px',
    'xl': '32px',
    'border_radius': '6px',
    'border_radius_small': '4px'
}


class YamlStyleLoader:
    """بارگذاری و مدیریت تنظیمات استایل از YAML"""
    
    def __init__(self, config_dir: str = None):
        # تعیین مسیر صحیح config - FIXED
        if config_dir is None:
            # مسیر مطلق از محل فایل اسکریپت
            script_dir = Path(__file__).parent.absolute()
            project_root = script_dir.parent
            self.config_dir = project_root / "config" / "ui"
        else:
            self.config_dir = Path(config_dir)
            
        print(f"🔍 مسیر config جستجو شده: {self.config_dir}")
        print(f"🔍 مسیر مطلق: {self.config_dir.absolute()}")
        print(f"🔍 وجود دارد: {self.config_dir.exists()}")
        
        self.colors_data: Dict[str, Any] = {}
        self.typography_data: Dict[str, Any] = {}
        self.spacing_data: Dict[str, Any] = {}
        self._loaded = False
        
    def load_all(self) -> bool:
        """بارگذاری تمام فایل‌های YAML"""
        try:
            # بررسی وجود پوشه
            if not self.config_dir.exists():
                logger.error(f"❌ پوشه config/ui یافت نشد: {self.config_dir}")
                print(f"❌ پوشه config/ui یافت نشد: {self.config_dir}")
                print(f"📁 دایرکتوری فعلی: {Path.cwd()}")
                return False
            
            print(f"✅ پوشه config/ui پیدا شد")
            
            # بارگذاری رنگ‌ها
            colors_path = self.config_dir / "colors.yaml"
            if colors_path.exists():
                with open(colors_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.colors_data = data if data else {}
                    print(f"✅ رنگ‌ها بارگذاری شد: {colors_path.name}")
            else:
                print(f"❌ فایل رنگ‌ها یافت نشد: {colors_path}")
                return False
            
            # بارگذاری تایپوگرافی
            typography_path = self.config_dir / "typography.yaml"
            if typography_path.exists():
                with open(typography_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.typography_data = data if data else {}
                    print(f"✅ تایپوگرافی بارگذاری شد: {typography_path.name}")
            else:
                print(f"❌ فایل تایپوگرافی یافت نشد: {typography_path}")
                return False
            
            # بارگذاری فاصله‌ها
            spacing_path = self.config_dir / "spacing.yaml"
            if spacing_path.exists():
                with open(spacing_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.spacing_data = data if data else {}
                    print(f"✅ فاصله‌ها بارگذاری شد: {spacing_path.name}")
            else:
                print(f"❌ فایل فاصله‌ها یافت نشد: {spacing_path}")
                return False
            
            self._loaded = True
            print("🎨 تمامی تنظیمات UI بارگذاری شدند")
            return True
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری YAML: {str(e)}")
            return False
    
    def get_nested_value(self, data: Dict, path: str, default: Any = None) -> Any:
        """دریافت مقدار از دیکشنری با مسیر سلسله‌مراتبی"""
        if not data:
            return default
            
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_color(self, path: str, default: str = None) -> str:
        """دریافت رنگ از تنظیمات YAML"""
        if not self._loaded:
            if not self.load_all():
                if default is not None:
                    return default
                # fallback به مقادیر پیش‌فرض
                color_map = {
                    'primary.main': DEFAULT_COLORS['primary'],
                    'primary.light': DEFAULT_COLORS['primary_light'],
                    'primary.dark': DEFAULT_COLORS['primary_dark'],
                    'secondary.main': DEFAULT_COLORS['secondary'],
                    'secondary.light': DEFAULT_COLORS['secondary_light'],
                    'secondary.dark': DEFAULT_COLORS['secondary_dark'],
                    'semantic.success': DEFAULT_COLORS['success'],
                    'semantic.warning': DEFAULT_COLORS['warning'],
                    'semantic.danger': DEFAULT_COLORS['danger'],
                    'background.primary': DEFAULT_COLORS['background'],
                    'text.primary': DEFAULT_COLORS['text_primary'],
                    'neutral.gray': DEFAULT_COLORS['border']
                }
                return color_map.get(path, '#000000')
        
        # مسیر کامل در YAML
        full_path = f"palette.{path}" if not path.startswith("palette.") else path
        
        # تلاش برای دریافت از YAML
        value = self.get_nested_value(self.colors_data, full_path)
        
        if isinstance(value, str) and value.startswith('#'):
            return value
        
        # fallback به default یا مقادیر پیش‌فرض
        if default is not None:
            return default
        
        return '#000000'
    
    def get_font_setting(self, setting: str, default: Any = None) -> Any:
        """دریافت تنظیم فونت"""
        if not self._loaded:
            if not self.load_all():
                return default if default is not None else DEFAULT_TYPOGRAPHY.get(setting, 'B Nazanin')
        
        # اول از YAML بگیر
        if setting in ['body', 'h1', 'h2', 'h3', 'small', 'tiny']:
            value = self.get_nested_value(self.typography_data, f"sizes.{setting}")
            if value is not None:
                return value
        
        value = self.get_nested_value(self.typography_data, f"fonts.{setting}")
        if value is not None:
            return value
        
        # fallback
        return default if default is not None else DEFAULT_TYPOGRAPHY.get(setting, 'B Nazanin')
    
    def get_spacing(self, size: str, default: str = None) -> str:
        """دریافت فاصله"""
        if not self._loaded:
            if not self.load_all():
                return default if default is not None else DEFAULT_SPACING.get(size, '8px')
        
        value = self.get_nested_value(self.spacing_data, f"spacing.{size}")
        if value is not None:
            return str(value)
        
        # همچنین border radius را بررسی کن
        if 'radius' in size or 'border' in size:
            radius_value = self.get_nested_value(self.spacing_data, f"borders.{size}")
            if radius_value is not None:
                return str(radius_value)
        
        return default if default is not None else DEFAULT_SPACING.get(size, '8px')
    
    def generate_complete_stylesheet(self) -> str:
        """تولید کامل استایل‌شیت Qt از تمام تنظیمات"""
        if not self._loaded:
            if not self.load_all():
                # حالت fallback
                gen_time = datetime.now().strftime('%Y/%m/%d %H:%M')
                return f"""/* استایل‌شیت پیش‌فرض - تولید در {gen_time} */
QMainWindow {{ background-color: {DEFAULT_COLORS['background']}; }}
QPushButton {{ background-color: {DEFAULT_COLORS['primary']}; color: white; }}"""
        
        # دریافت مقادیر با fallback
        primary = self.get_color("primary.main")
        primary_light = self.get_color("primary.light")
        primary_dark = self.get_color("primary.dark")
        secondary = self.get_color("secondary.main")
        background = self.get_color("background.primary")
        text_primary = self.get_color("text.primary")
        success = self.get_color("semantic.success")
        warning = self.get_color("semantic.warning")
        danger = self.get_color("semantic.danger")
        
        font_family = self.get_font_setting("primary")
        font_size = self.get_font_setting("body")
        
        spacing_xs = self.get_spacing("xs")
        spacing_sm = self.get_spacing("sm")
        spacing_md = self.get_spacing("md")
        spacing_lg = self.get_spacing("lg")
        
        # دریافت border radius
        border_radius = self.get_spacing("radius.small") or self.get_spacing("border_radius.small") or "4px"
        
        # تاریخ تولید
        gen_time = datetime.now().strftime('%Y/%m/%d %H:%M')
        
        # تولید استایل‌شیت
        qss = f"""
/* ===== استایل‌شیت سیستم فست‌فود ===== */
/* تولید شده در {gen_time} */
/* از فایل‌های YAML: colors.yaml, typography.yaml, spacing.yaml */

/* پنجره اصلی */
QMainWindow, QDialog {{
    background-color: {background};
    color: {text_primary};
    font-family: "{font_family}";
    font-size: {font_size}px;
}}

/* دکمه‌ها */
QPushButton {{
    background-color: {primary};
    color: white;
    border-radius: {border_radius};
    padding: {spacing_sm} {spacing_md};
    font-weight: bold;
    border: none;
}}

QPushButton:hover {{
    background-color: {primary_light};
}}

QPushButton:pressed {{
    background-color: {primary_dark};
}}

/* برچسب‌ها */
QLabel {{
    color: {text_primary};
    font-size: {font_size}px;
    padding: {spacing_sm};
}}

/* فیلدهای ورودی */
QLineEdit, QTextEdit, QComboBox {{
    border: 1px solid {self.get_color("neutral.gray")};
    border-radius: {border_radius};
    padding: {spacing_xs} {spacing_sm};
    background-color: white;
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 2px solid {primary};
}}

/* جدول */
QTableWidget {{
    gridline-color: {self.get_color("neutral.light_gray", "#E9ECEF")};
}}

QHeaderView::section {{
    background-color: {self.get_color("neutral.light", "#F8F9FA")};
    padding: {spacing_sm};
    border: 1px solid {self.get_color("neutral.light_gray", "#E9ECEF")};
    font-weight: bold;
}}
"""
        return qss


def build_stylesheet(use_yaml: bool = True) -> str:
    """
    رابط اصلی برای ساخت استایل‌شیت
    
    Returns:
        رشته استایل‌شیت QSS
    """
    if use_yaml:
        try:
            loader = YamlStyleLoader()
            stylesheet = loader.generate_complete_stylesheet()
            print("✅ استایل‌شیت از YAML تولید شد")
            return stylesheet
        except Exception as e:
            print(f"⚠️ خطا در تولید از YAML: {e}")
    
    # حالت fallback
    print("ℹ️ استفاده از استایل‌های پیش‌فرض")
    gen_time = datetime.now().strftime('%Y/%m/%d %H:%M')
    
    return f"""
/* استایل‌شیت پیش‌فرض - تولید در {gen_time} */
QMainWindow {{
    background-color: {DEFAULT_COLORS['background']};
    color: {DEFAULT_COLORS['text_primary']};
    font-family: "{DEFAULT_TYPOGRAPHY['font_primary']}";
    font-size: {DEFAULT_TYPOGRAPHY['font_size_normal']}px;
}}

QPushButton {{
    background-color: {DEFAULT_COLORS['primary']};
    color: white;
    border-radius: {DEFAULT_SPACING['border_radius']};
    padding: {DEFAULT_SPACING['sm']} {DEFAULT_SPACING['md']};
}}

QLineEdit {{
    border: 1px solid {DEFAULT_COLORS['border']};
    border-radius: {DEFAULT_SPACING['border_radius_small']};
    padding: {DEFAULT_SPACING['xs']};
}}
"""


def test_system():
    """تست سیستم استایل"""
    print("=" * 50)
    print("🧪 تست سیستم استایل")
    print("=" * 50)
    
    loader = YamlStyleLoader()
    
    if loader.load_all():
        print("✅ تنظیمات بارگذاری شدند")
        
        # تست مقادیر
        tests = [
            ("رنگ اصلی", loader.get_color("primary.main")),
            ("فونت", loader.get_font_setting("primary")),
            ("سایز متن", loader.get_font_setting("body")),
            ("فاصله sm", loader.get_spacing("sm"))
        ]
        
        for name, value in tests:
            print(f"  {name}: {value}")
        
        # تولید استایل
        stylesheet = loader.generate_complete_stylesheet()
        
        # ذخیره
        output_file = "generated_style.qss"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(stylesheet)
        
        print(f"\n📄 استایل‌شیت تولید شد")
        print(f"  اندازه: {len(stylesheet):,} کاراکتر")
        print(f"  ذخیره در: {output_file}")
        
        return True
    else:
        print("❌ خطا در بارگذاری تنظیمات")
        return False


if __name__ == "__main__":
    # غیرفعال کردن لاگ‌های اضافی
    logging.basicConfig(level=logging.CRITICAL)
    
    # اجرای تست
    if test_system():
        print("\n✅ سیستم استایل آماده است")
    else:
        print("\n⚠️ استفاده از حالت fallback")
    
    # خروجی نهایی
    qss = build_stylesheet(use_yaml=True)
    print(f"\n🎨 استایل‌شیت نهایی: {len(qss):,} کاراکتر")