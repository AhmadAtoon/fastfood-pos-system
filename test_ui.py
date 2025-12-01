# test_ui.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from styles.style_builder import build_stylesheet

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تست سیستم استایل فست‌فود")
        self.setGeometry(100, 100, 400, 300)
        
        # ایجاد ویجت مرکزی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # ایجاد لایوت
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # اضافه کردن ویجت‌های تست
        label = QLabel("🚀 سیستم فست‌فود - تست استایل")
        button1 = QPushButton("دکمه اصلی")
        button2 = QPushButton("دکمه ثانویه")
        
        layout.addWidget(label)
        layout.addWidget(button1)
        layout.addWidget(button2)

def main():
    app = QApplication(sys.argv)
    
    # اعمال استایل‌شیت
    stylesheet = build_stylesheet(use_yaml=True)
    app.setStyleSheet(stylesheet)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()