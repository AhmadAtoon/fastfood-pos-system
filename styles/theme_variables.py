"""
theme_variables.py
مدیریت متمرکز متغیرهای تم سیستم از فایل‌های پیکربندی YAML
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ThemeVariables:
    """کلاس مدیریت متغیرهای تم"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        مقداردهی اولیه
        
        Args:
            config_dir: مسیر دایرکتوری config (پیش‌فرض: config/ui در ریشه پروژه)
        """
        if config_dir is None:
            # پیدا کردن مسیر config/ui به صورت هوشمند
            current_file = Path(__file__).absolute()
            if current_file.parent.name == 'styles':
                project_root = current_file.parent.parent
            else:
                project_root = current_file.parent
            self.config_dir = project_root / "config" / "ui"
        else:
            self.config_dir = Path(config_dir)
            
        self.variables: Dict[str, Any] = {}
        self._loaded = False
        
    def load_all(self) -> bool:
        """
        بارگذاری تمام متغیرها از فایل‌های YAML
        
        Returns:
            bool: موفقیت‌آمیز بودن بارگذاری
        """
        try:
            if not self.config_dir.exists():
                logger.error(f"پوشه config یافت نشد: {self.config_dir}")
                return False
            
            # بارگذاری رنگ‌ها
            colors_path = self.config_dir / "colors.yaml"
            if colors_path.exists():
                with open(colors_path, 'r', encoding='utf-8') as f:
                    colors_data = yaml.safe_load(f) or {}
                    self.variables['colors'] = colors_data.get('palette', {})
            else:
                logger.warning(f"فایل colors.yaml یافت نشد: {colors_path}")
                return False
            
            # بارگذاری تایپوگرافی
            typography_path = self.config_dir / "typography.yaml"
            if typography_path.exists():
                with open(typography_path, 'r', encoding='utf-8') as f:
                    typography_data = yaml.safe_load(f) or {}
                    self.variables['typography'] = {
                        'fonts': typography_data.get('fonts', {}),
                        'sizes': typography_data.get('sizes', {}),
                        'weights': typography_data.get('weights', {}),
                        'rtl': typography_data.get('rtl_settings', {})
                    }
            else:
                logger.warning(f"فایل typography.yaml یافت نشد: {typography_path}")
                return False
            
            # بارگذاری فاصله‌ها
            spacing_path = self.config_dir / "spacing.yaml"
            if spacing_path.exists():
                with open(spacing_path, 'r', encoding='utf-8') as f:
                    spacing_data = yaml.safe_load(f) or {}
                    self.variables['spacing'] = {
                        'units': spacing_data.get('units', {}),
                        'spacing': spacing_data.get('spacing', {}),
                        'borders': spacing_data.get('borders', {}),
                        'shadows': spacing_data.get('shadows', {})
                    }
            else:
                logger.warning(f"فایل spacing.yaml یافت نشد: {spacing_path}")
                return False
            
            self._loaded = True
            logger.info("تمامی متغیرهای تم با موفقیت بارگذاری شدند")
            return True
            
        except Exception as e:
            logger.error(f"خطا در بارگذاری متغیرهای تم: {str(e)}")
            return False
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        دریافت یک متغیر با مسیر نقطه‌ای
        
        Args:
            path: مسیر متغیر (مثلا 'colors.primary.main')
            default: مقدار پیش‌فرض در صورت یافت نشدن
            
        Returns:
            مقدار متغیر یا مقدار پیش‌فرض
        """
        if not self._loaded:
            if not self.load_all():
                return default
        
        keys = path.split('.')
        current = self.variables
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_color(self, color_path: str, default: str = '#000000') -> str:
        """
        دریافت یک رنگ
        
        Args:
            color_path: مسیر رنگ (مثلا 'primary.main')
            default: رنگ پیش‌فرض
            
        Returns:
            رشته رنگ هگز
        """
        full_path = f"colors.{color_path}"
        color = self.get(full_path, default)
        
        if isinstance(color, str) and color.startswith('#'):
            return color
        return default
    
    def get_font(self, font_key: str = 'primary', default: str = 'B Nazanin') -> str:
        """
        دریافت نام فونت
        
        Args:
            font_key: کلید فونت ('primary', 'fallbacks', 'monospace')
            default: فونت پیش‌فرض
            
        Returns:
            نام فونت
        """
        font = self.get(f"typography.fonts.{font_key}", default)
        return str(font)
    
    def get_font_size(self, size_key: str = 'body', default: int = 14) -> int:
        """
        دریافت سایز فونت
        
        Args:
            size_key: کلید سایز ('h1', 'h2', 'body', 'small', ...)
            default: سایز پیش‌فرض
            
        Returns:
            سایز فونت به عدد
        """
        size = self.get(f"typography.sizes.{size_key}", default)
        try:
            return int(size)
        except (ValueError, TypeError):
            return default
    
    def get_spacing(self, spacing_key: str, default: str = '8px') -> str:
        """
        دریافت فاصله
        
        Args:
            spacing_key: کلید فاصله ('xs', 'sm', 'md', 'lg', ...)
            default: فاصله پیش‌فرض
            
        Returns:
            فاصله با واحد
        """
        spacing = self.get(f"spacing.spacing.{spacing_key}", default)
        return str(spacing)
    
    def get_border_radius(self, radius_key: str = 'small', default: str = '4px') -> str:
        """
        دریافت border radius
        
        Args:
            radius_key: کلید radius ('small', 'medium', 'large')
            default: مقدار پیش‌فرض
            
        Returns:
            radius با واحد
        """
        radius = self.get(f"spacing.borders.radius.{radius_key}", default)
        return str(radius)
    
    def get_shadow(self, shadow_key: str = 'level1', default: str = '0 1px 3px rgba(0,0,0,0.12)') -> str:
        """
        دریافت سایه
        
        Args:
            shadow_key: کلید سایه ('level1', 'level2', 'level3', 'level4')
            default: سایه پیش‌فرض
            
        Returns:
            رشته سایه CSS
        """
        shadow = self.get(f"spacing.shadows.{shadow_key}", default)
        return str(shadow)
    
    def get_all_colors(self) -> Dict[str, Any]:
        """دریافت تمام رنگ‌ها"""
        return self.get('colors', {})
    
    def get_all_typography(self) -> Dict[str, Any]:
        """دریافت تمام تنظیمات تایپوگرافی"""
        return self.get('typography', {})
    
    def get_all_spacing(self) -> Dict[str, Any]:
        """دریافت تمام تنظیمات فاصله"""
        return self.get('spacing', {})
    
    def reload(self) -> bool:
        """بارگذاری مجدد متغیرها"""
        self.variables.clear()
        self._loaded = False
        return self.load_all()
    
    def export_as_dict(self) -> Dict[str, Any]:
        """
        صادر کردن تمام متغیرها به عنوان دیکشنری
        
        Returns:
            دیکشنری کامل متغیرها
        """
        if not self._loaded:
            self.load_all()
        return self.variables.copy()


# ایجاد نمونه اصلی برای استفاده در سراسر برنامه
theme = ThemeVariables()

# توابع کمکی برای دسترسی سریع
def get_color(path: str, default: str = '#000000') -> str:
    return theme.get_color(path, default)

def get_font(font_key: str = 'primary', default: str = 'B Nazanin') -> str:
    return theme.get_font(font_key, default)

def get_font_size(size_key: str = 'body', default: int = 14) -> int:
    return theme.get_font_size(size_key, default)

def get_spacing(spacing_key: str, default: str = '8px') -> str:
    return theme.get_spacing(spacing_key, default)


if __name__ == "__main__":
    # تست ساده
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 تست theme_variables.py")
    print("=" * 50)
    
    if theme.load_all():
        print("✅ متغیرهای تم بارگذاری شدند")
        
        # تست‌های نمونه
        tests = [
            ("رنگ اصلی", theme.get_color("primary.main")),
            ("فونت اصلی", theme.get_font("primary")),
            ("سایز متن", theme.get_font_size("body")),
            ("فاصله متوسط", theme.get_spacing("md")),
            ("border radius کوچک", theme.get_border_radius("small")),
            ("سایه سطح ۱", theme.get_shadow("level1"))
        ]
        
        for name, value in tests:
            print(f"  {name}: {value}")
        
        print(f"\n📊 تعداد متغیرهای بارگذاری شده:")
        print(f"  رنگ‌ها: {len(theme.get_all_colors())} دسته")
        print(f"  تنظیمات فونت: {len(theme.get_all_typography())} بخش")
        print(f"  فاصله‌ها: {len(theme.get_all_spacing())} بخش")
        
        print("\n✅ theme_variables.py آماده است")
    else:
        print("❌ خطا در بارگذاری متغیرهای تم")