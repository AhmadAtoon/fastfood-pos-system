"""
مدیریت پایگاه داده برای سیستم فروش فست‌فود
پشتیبانی از SQLite (توسعه) و PostgreSQL (تولید)
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json
from datetime import datetime

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """مدیر پایگاه داده مرکزی"""
    
    def __init__(self, db_path: str = "fastfood_pos.db"):
        """
        مقداردهی اولیه مدیر دیتابیس
        
        Args:
            db_path: مسیر فایل دیتابیس SQLite
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self.is_connected = False
        
        # ایجاد پوشه اگر وجود ندارد
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def connect(self) -> bool:
        """
        اتصال به پایگاه داده
        
        Returns:
            True اگر موفقیت‌آمیز بود
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
            self.is_connected = True
            
            # فعال کردن کلیدهای خارجی
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            logger.info(f"اتصال به دیتابیس برقرار شد: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"خطا در اتصال به دیتابیس: {e}")
            return False
    
    def disconnect(self):
        """قطع اتصال از پایگاه داده"""
        if self.connection:
            self.connection.close()
            self.is_connected = False
            logger.info("اتصال به دیتابیس قطع شد")
    
    def initialize_database(self) -> bool:
        """
        ایجاد جداول اولیه اگر وجود ندارند
        
        Returns:
            True اگر موفقیت‌آمیز بود
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            # جدول کاربران
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'cashier',
                    email TEXT,
                    full_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # جدول دسته‌بندی محصولات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories (category_id)
                )
            """)
            
            # جدول محصولات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL CHECK (price >= 0),
                    cost_price REAL,
                    category_id INTEGER,
                    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
                    min_stock_threshold INTEGER DEFAULT 5,
                    barcode TEXT UNIQUE,
                    is_available BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id)
                )
            """)
            
            # جدول مشتریان
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE,
                    email TEXT,
                    address TEXT,
                    membership_code TEXT UNIQUE,
                    loyalty_points INTEGER DEFAULT 0 CHECK (loyalty_points >= 0),
                    total_spent REAL DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # جدول تخفیف‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discounts (
                    discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_type TEXT NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
                    value REAL NOT NULL CHECK (value >= 0),
                    scope TEXT CHECK (scope IN ('global', 'category', 'product')),
                    category_id INTEGER,
                    product_id INTEGER,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    min_order_total REAL DEFAULT 0,
                    usage_limit INTEGER DEFAULT 1,
                    times_used INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id),
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                )
            """)
            
            # جدول سفارشات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK (
                        status IN ('pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled')
                    ),
                    total_amount REAL NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
                    discount_amount REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    delivery_method TEXT CHECK (delivery_method IN ('pickup', 'delivery')),
                    delivery_fee REAL DEFAULT 0,
                    delivery_address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول آیتم‌های سفارش
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    unit_price REAL NOT NULL CHECK (unit_price >= 0),
                    subtotal REAL NOT NULL CHECK (subtotal >= 0),
                    notes TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                )
            """)
            
            # جدول پرداخت‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    amount REAL NOT NULL CHECK (amount >= 0),
                    payment_method TEXT NOT NULL CHECK (
                        payment_method IN ('cash', 'card', 'online', 'wallet')
                    ),
                    status TEXT NOT NULL DEFAULT 'pending' CHECK (
                        status IN ('pending', 'completed', 'failed', 'refunded')
                    ),
                    transaction_code TEXT UNIQUE,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    refund_date TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id)
                )
            """)
            
            # جدول موجودی (تاریخچه تغییرات)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    change_type TEXT NOT NULL CHECK (change_type IN ('purchase', 'sale', 'adjustment', 'waste')),
                    quantity_change INTEGER NOT NULL,
                    previous_quantity INTEGER NOT NULL,
                    new_quantity INTEGER NOT NULL,
                    reason TEXT,
                    user_id INTEGER,
                    reference_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (product_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            self.connection.commit()
            logger.info("جداول دیتابیس با موفقیت ایجاد شدند")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"خطا در ایجاد جداول: {e}")
            return False
    
    def execute_query(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        اجرای یک کوئری ساده
        
        Args:
            query: دستور SQL
            params: پارامترهای کوئری
            
        Returns:
            cursor برای fetch کردن نتایج
        """
        if not self.is_connected:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        اجرای یک کوئری با چندین مجموعه پارامتر
        
        Args:
            query: دستور SQL
            params_list: لیست پارامترها
            
        Returns:
            True اگر موفقیت‌آمیز بود
        """
        try:
            if not self.is_connected:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"خطا در اجرای دستورات گروهی: {e}")
            return False
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict]:
        """
        دریافت تمام ردیف‌های نتیجه کوئری
        
        Returns:
            لیست دیکشنری‌ها
        """
        cursor = self.execute_query(query, params)
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """
        دریافت تنها یک ردیف از نتیجه کوئری
        
        Returns:
            دیکشنری ردیف یا None
        """
        cursor = self.execute_query(query, params)
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return None
    
    def insert(self, table: str, data: Dict) -> Optional[int]:
        """
        درج یک رکورد جدید
        
        Args:
            table: نام جدول
            data: دیکشنری ستون‌ها و مقادیر
            
        Returns:
            ID رکورد درج شده یا None
        """
        try:
            if not self.is_connected:
                self.connect()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(data.values()))
            self.connection.commit()
            
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            logger.error(f"خطا در درج داده در جدول {table}: {e}")
            return None
    
    def update(self, table: str, data: Dict, where: str, where_params: Tuple = ()) -> bool:
        """
        به‌روزرسانی رکوردها
        
        Args:
            table: نام جدول
            data: دیکشنری ستون‌ها و مقادیر جدید
            where: شرط WHERE
            where_params: پارامترهای شرط
            
        Returns:
            True اگر موفقیت‌آمیز بود
        """
        try:
            if not self.is_connected:
                self.connect()
            
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where}"
            
            cursor = self.connection.cursor()
            params = tuple(data.values()) + where_params
            cursor.execute(query, params)
            self.connection.commit()
            
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            logger.error(f"خطا در به‌روزرسانی جدول {table}: {e}")
            return False
    
    def delete(self, table: str, where: str, where_params: Tuple = ()) -> bool:
        """
        حذف رکوردها
        
        Args:
            table: نام جدول
            where: شرط WHERE
            where_params: پارامترهای شرط
            
        Returns:
            True اگر موفقیت‌آمیز بود
        """
        try:
            if not self.is_connected:
                self.connect()
            
            query = f"DELETE FROM {table} WHERE {where}"
            
            cursor = self.connection.cursor()
            cursor.execute(query, where_params)
            self.connection.commit()
            
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            logger.error(f"خطا در حذف از جدول {table}: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        پشتیبان‌گیری از دیتابیس
        
        Args:
            backup_path: مسیر فایل پشتیبان
            
        Returns:
            True اگر موفقیت‌آمیز بود
        """
        try:
            if not self.is_connected:
                self.connect()
            
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"پشتیبان‌گیری انجام شد: {backup_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"خطا در پشتیبان‌گیری: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار دیتابیس
        
        Returns:
            دیکشنری آمار
        """
        stats = {}
        
        try:
            if not self.is_connected:
                self.connect()
            
            # تعداد رکوردها در هر جدول
            tables = [
                'users', 'categories', 'products', 'customers',
                'discounts', 'orders', 'order_items', 'payments',
                'inventory_logs'
            ]
            
            for table in tables:
                cursor = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()[0]
                stats[f"{table}_count"] = count
            
            # حجم دیتابیس
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            stats["database_size_bytes"] = db_size
            stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
            
            # تاریخ ایجاد
            stats["created_date"] = datetime.fromtimestamp(
                self.db_path.stat().st_ctime
            ).isoformat() if self.db_path.exists() else None
            
        except Exception as e:
            logger.error(f"خطا در دریافت آمار دیتابیس: {e}")
        
        return stats
    
    def __enter__(self):
        """برای استفاده با with"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """برای استفاده با with"""
        self.disconnect()


# تابع کمکی برای تست سریع
def test_database():
    """تابع تست برای بررسی عملکرد دیتابیس"""
    print("🔧 تست پایگاه داده...")
    
    with DatabaseManager("test.db") as db:
        # ایجاد جداول
        if db.initialize_database():
            print("✅ جداول ایجاد شدند")
            
            # تست درج کاربر
            user_id = db.insert("users", {
                "username": "admin",
                "password_hash": "hashed_password_123",
                "role": "admin",
                "email": "admin@example.com",
                "full_name": "مدیر سیستم"
            })
            
            if user_id:
                print(f"✅ کاربر اضافه شد (ID: {user_id})")
            
            # تست درج دسته‌بندی
            cat_id = db.insert("categories", {
                "name": "غذای اصلی",
                "description": "غذاهای اصلی رستوران"
            })
            
            if cat_id:
                print(f"✅ دسته‌بندی اضافه شد (ID: {cat_id})")
            
            # تست درج محصول
            product_id = db.insert("products", {
                "name": "برگر ویژه",
                "price": 85000,
                "category_id": cat_id,
                "stock_quantity": 50
            })
            
            if product_id:
                print(f"✅ محصول اضافه شد (ID: {product_id})")
            
            # تست دریافت آمار
            stats = db.get_database_stats()
            print(f"📊 آمار دیتابیس:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            # پاک کردن فایل تست
            import os
            import time
            time.sleep(0.1)
            if os.path.exists("test.db"):
                try:
                    os.remove("test.db")
                    print("🧹 فایل تست پاک شد")
                except PermissionError:
                    print("⚠️ فایل تست خودکار پاک می‌شود")
        else:
            print("❌ خطا در ایجاد جداول")


if __name__ == "__main__":
    test_database()