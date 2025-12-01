#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکنر هوشمند کد - Smart Code Scanner PRO - نسخه کامل یکپارچه
"""

import os
import ast
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SmartCodeScannerPRO:
    def __init__(self):
        self.target_folders = [
            "analytics",
            "exports", 
            "i18n",
            "models",
            "reports",
            "quality"
        ]
        self.scan_id = None
        self.output_dir = "scan_reports"
        
    def scan_project(self, project_path: str) -> Dict[str, Any]:
        """اسکن کامل پروژه و ذخیره گزارش"""
        # ایجاد شناسه و پوشه خروجی
        self.scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"🎯 شروع اسکن پروژه: {project_path}")
        
        project_data = {
            "scan_info": {
                "scan_id": self.scan_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "project_path": project_path,
                "target_folders": self.target_folders
            },
            "project_stats": {
                "total_files": 0,
                "analyzed_files": 0,
                "successful_files": 0,
                "failed_files": 0
            },
            "code_analysis": {
                "classes": 0,
                "functions": 0,
                "methods": 0,
                "lines_of_code": 0,
                "docstrings": 0,
                "comments": 0
            },
            "folders": {},
            "files_details": []
        }
        
        # اسکن هر پوشه
        for folder in self.target_folders:
            folder_path = os.path.join(project_path, folder)
            if os.path.exists(folder_path):
                print(f"📁 اسکن پوشه: {folder}")
                folder_data = self._scan_folder(folder_path, folder)
                project_data["folders"][folder] = folder_data
                
                # جمع‌آوری آمار
                project_data["project_stats"]["total_files"] += folder_data["file_count"]
                project_data["project_stats"]["analyzed_files"] += folder_data["analyzed_files"]
                project_data["project_stats"]["successful_files"] += folder_data["successful_files"]
                project_data["project_stats"]["failed_files"] += folder_data["failed_files"]
                
                # استفاده از فیلدهای count
                project_data["code_analysis"]["classes"] += folder_data["analysis"]["classes"]
                project_data["code_analysis"]["functions"] += folder_data["analysis"]["functions"]
                project_data["code_analysis"]["methods"] += folder_data["analysis"]["methods"]
                project_data["code_analysis"]["lines_of_code"] += folder_data["analysis"]["lines_of_code"]
                project_data["code_analysis"]["docstrings"] += folder_data["analysis"]["docstrings"]
                project_data["code_analysis"]["comments"] += folder_data["analysis"]["comments"]
        
        # ذخیره گزارش کامل
        self._save_full_report(project_data)
        
        # ایجاد گزارش خلاصه
        self._create_summary_report(project_data)
        
        # بررسی وضعیت اسکن
        scan_status = self._verify_scan_completion(project_data)
        project_data["scan_info"]["status"] = scan_status["status"]
        project_data["scan_info"]["success_rate"] = scan_status["success_rate"]
        
        print(f"✅ اسکن کامل شد! وضعیت: {scan_status['status']}")
        
        return project_data
    
    def _scan_folder(self, folder_path: str, folder_name: str) -> Dict[str, Any]:
        """اسکن یک پوشه خاص"""
        folder_data = {
            "folder_name": folder_name,
            "folder_path": folder_path,
            "file_count": 0,
            "analyzed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "analysis": {
                "classes": 0,
                "functions": 0,
                "methods": 0,
                "lines_of_code": 0,
                "docstrings": 0,
                "comments": 0
            },
            "files": []
        }
        
        py_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        
        folder_data["file_count"] = len(py_files)
        
        for file_path in py_files:
            file_data = self._analyze_file(file_path)
            folder_data["analyzed_files"] += 1
            
            if "error" not in file_data:
                folder_data["successful_files"] += 1
                # استفاده از فیلدهای count به جای لیست‌ها
                folder_data["analysis"]["classes"] += file_data.get("classes_count", 0)
                folder_data["analysis"]["functions"] += file_data.get("functions_count", 0)
                folder_data["analysis"]["methods"] += file_data.get("methods_count", 0)
                folder_data["analysis"]["lines_of_code"] += file_data.get("lines_of_code", 0)
                folder_data["analysis"]["docstrings"] += file_data.get("docstrings_count", 0)
                folder_data["analysis"]["comments"] += file_data.get("comments_count", 0)
            else:
                folder_data["failed_files"] += 1
            
            folder_data["files"].append(file_data)
        
        return folder_data
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """تحلیل دقیق یک فایل پایتون"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_data = {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "lines_of_code": len(content.splitlines()),
                "classes_count": 0,
                "functions_count": 0,
                "methods_count": 0,
                "docstrings_count": 0,
                "comments_count": 0
            }
            
            # تحلیل AST
            try:
                tree = ast.parse(content)
                
                # استخراج کلاس‌ها
                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_info = {
                            "name": node.name,
                            "line_number": node.lineno,
                            "methods": [],
                            "docstring": ast.get_docstring(node)
                        }
                        
                        # متدهای کلاس
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                method_info = {
                                    "name": item.name,
                                    "line_number": item.lineno,
                                    "args": [arg.arg for arg in item.args.args],
                                    "docstring": ast.get_docstring(item)
                                }
                                class_info["methods"].append(method_info)
                        
                        classes.append(class_info)
                
                file_data["classes"] = classes
                file_data["classes_count"] = len(classes)
                file_data["methods_count"] = sum(len(cls["methods"]) for cls in classes)
                
                # استخراج توابع
                functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # فقط توابع سطح ماژول (نه متدهای کلاس)
                        if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                            func_info = {
                                "name": node.name,
                                "line_number": node.lineno,
                                "args": [arg.arg for arg in node.args.args],
                                "docstring": ast.get_docstring(node)
                            }
                            functions.append(func_info)
                
                file_data["functions"] = functions
                file_data["functions_count"] = len(functions)
                
                # استخراج docstring‌ها
                docstrings = []
                for node in ast.walk(tree):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        docstrings.append({
                            "type": type(node).__name__,
                            "line": getattr(node, 'lineno', 'N/A'),
                            "content": docstring[:100] + "..." if len(docstring) > 100 else docstring
                        })
                
                file_data["docstrings"] = docstrings
                file_data["docstrings_count"] = len(docstrings)
                
                # استخراج کامنت‌ها (ساده)
                comments = []
                lines = content.splitlines()
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith('#') and not stripped_line.startswith('#' * 80):
                        comments.append(stripped_line)
                
                file_data["comments"] = comments
                file_data["comments_count"] = len(comments)
                
                # محتوای نمونه
                file_data["content_preview"] = content[:500] + "..." if len(content) > 500 else content
                
            except SyntaxError as e:
                file_data["error"] = f"SyntaxError: {e}"
                file_data["error_type"] = "SyntaxError"
            
            return file_data
            
        except Exception as e:
            return {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _save_full_report(self, project_data: Dict[str, Any]):
        """ذخیره گزارش کامل JSON"""
        report_filename = f"code_scan_report_{self.scan_id}.json"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 گزارش کامل ذخیره شد: {report_path}")
        return report_path
    
    def _create_summary_report(self, project_data: Dict[str, Any]):
        """ایجاد گزارش خلاصه متنی"""
        summary_filename = f"scan_summary_{self.scan_id}.txt"
        summary_path = os.path.join(self.output_dir, summary_filename)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("🎯 گزارش کامل اسکن کد - Smart Code Scanner PRO\n")
            f.write("=" * 70 + "\n\n")
            
            # اطلاعات اسکن
            f.write("📋 اطلاعات اسکن:\n")
            f.write("-" * 40 + "\n")
            f.write(f"• شناسه اسکن: {project_data['scan_info']['scan_id']}\n")
            f.write(f"• زمان اسکن: {project_data['scan_info']['timestamp']}\n")
            f.write(f"• مسیر پروژه: {project_data['scan_info']['project_path']}\n")
            f.write(f"• وضعیت: {project_data['scan_info'].get('status', 'در حال پردازش')}\n")
            f.write(f"• نرخ موفقیت: {project_data['scan_info'].get('success_rate', 0):.1f}%\n\n")
            
            # آمار پروژه
            stats = project_data["project_stats"]
            f.write("📊 آمار پروژه:\n")
            f.write("-" * 40 + "\n")
            f.write(f"• کل فایل‌ها: {stats['total_files']}\n")
            f.write(f"• فایل‌های تحلیل شده: {stats['analyzed_files']}\n")
            f.write(f"• فایل‌های موفق: {stats['successful_files']}\n")
            f.write(f"• فایل‌های ناموفق: {stats['failed_files']}\n\n")
            
            # آنالیز کد
            analysis = project_data["code_analysis"]
            f.write("🔍 آنالیز کد:\n")
            f.write("-" * 40 + "\n")
            f.write(f"• کلاس‌ها: {analysis['classes']}\n")
            f.write(f"• توابع: {analysis['functions']}\n")
            f.write(f"• متدها: {analysis['methods']}\n")
            f.write(f"• خطوط کد: {analysis['lines_of_code']}\n")
            f.write(f"• Docstringها: {analysis['docstrings']}\n")
            f.write(f"• کامنت‌ها: {analysis['comments']}\n\n")
            
            # آمار پوشه‌ها
            f.write("📁 آمار پوشه‌ها:\n")
            f.write("-" * 40 + "\n")
            for folder_name, folder_data in project_data["folders"].items():
                f.write(f"• {folder_name}:\n")
                f.write(f"  - فایل‌ها: {folder_data['file_count']}\n")
                f.write(f"  - موفق: {folder_data['successful_files']}\n")
                f.write(f"  - ناموفق: {folder_data['failed_files']}\n")
                f.write(f"  - کلاس‌ها: {folder_data['analysis']['classes']}\n")
                f.write(f"  - توابع: {folder_data['analysis']['functions']}\n\n")
            
            f.write("✅ گزارش کامل در فایل JSON ذخیره شد.\n")
            f.write("📝 برای جزئیات بیشتر به فایل گزارش کامل مراجعه کنید.\n")
        
        print(f"📝 گزارش خلاصه ذخیره شد: {summary_path}")
        return summary_path
    
    def _verify_scan_completion(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """تأیید کامل بودن اسکن"""
        stats = project_data["project_stats"]
        
        if stats["total_files"] == 0:
            status = "ناموفق ❌ - هیچ فایلی یافت نشد"
            success_rate = 0
        elif stats["analyzed_files"] == stats["total_files"]:
            if stats["failed_files"] == 0:
                status = "کامل ✅ - تمام فایل‌ها با موفقیت تحلیل شدند"
                success_rate = 100.0
            else:
                status = "ناقص ⚠️ - برخی فایل‌ها تحلیل نشدند"
                success_rate = (stats["successful_files"] / stats["total_files"]) * 100
        else:
            status = "ناقص ❌ - اسکن کامل نشد"
            success_rate = (stats["analyzed_files"] / stats["total_files"]) * 100
        
        return {
            "status": status,
            "success_rate": success_rate,
            "is_complete": stats["analyzed_files"] == stats["total_files"] and stats["failed_files"] == 0
        }


class ScannerGUI_PRO:
    def __init__(self, root):
        self.root = root
        self.root.title("اسکنر هوشمند کد PRO - Smart Code Scanner PRO")
        self.root.geometry("1400x900")
        self.scanner = SmartCodeScannerPRO()
        self.project_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """راه‌اندازی رابط کاربری پیشرفته"""
        # فریم اصلی
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # تنظیم وزن‌ها
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # عنوان
        title_label = ttk.Label(main_frame, 
                               text="🔍 اسکنر هوشمند کد PRO - تحلیل 6 پوشه اصلی",
                               font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # بخش انتخاب پروژه
        ttk.Label(main_frame, text="🎯 مسیر پروژه:", font=("Arial", 12)).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(main_frame, textvariable=self.path_var, width=70, font=("Arial", 10))
        path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        browse_btn = ttk.Button(main_frame, text="📁 انتخاب پوشه", command=self.browse_folder)
        browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # دکمه‌های کنترلی
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=15)
        
        scan_btn = ttk.Button(button_frame, text="🚀 شروع اسکن هوشمند", command=self.start_scan)
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(button_frame, text="💾 ذخیره گزارش", command=self.export_report)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(button_frame, text="🗑️ پاکسازی", command=self.clear_results)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # نوار پیشرفت
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # وضعیت
        self.status_var = tk.StringVar(value="🟢 آماده برای اسکن...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 10, "bold"))
        status_label.grid(row=4, column=0, columnspan=3, pady=5)
        
        # نوت‌بوک برای نمایش نتایج
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # ایجاد تب‌ها
        self._create_summary_tab()
        self._create_folders_tab()
        self._create_code_tab()
        self._create_log_tab()
        
        # کنسول لاگ
        self.log_text = scrolledtext.ScrolledText(main_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        self.log_text.insert(tk.END, "📋 کنسول لاگ - منتظر شروع اسکن...\n")
        self.log_text.config(state=tk.DISABLED)
    
    def _create_summary_tab(self):
        """ایجاد تب خلاصه"""
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="📊 خلاصه پروژه")
        
        # Treeview برای نمایش خلاصه
        self.summary_tree = ttk.Treeview(self.summary_tab, columns=('Value', 'Status'), show='tree headings', height=20)
        self.summary_tree.heading('#0', text='معیار')
        self.summary_tree.heading('Value', text='مقدار')
        self.summary_tree.heading('Status', text='وضعیت')
        
        self.summary_tree.column('#0', width=300)
        self.summary_tree.column('Value', width=150)
        self.summary_tree.column('Status', width=100)
        
        self.summary_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_folders_tab(self):
        """ایجاد تب پوشه‌ها"""
        self.folders_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.folders_tab, text="📁 جزئیات پوشه‌ها")
        
        # Treeview برای پوشه‌ها
        self.folders_tree = ttk.Treeview(self.folders_tab, columns=('Files', 'Success', 'Failed', 'Classes', 'Functions'), 
                                       show='tree headings', height=20)
        self.folders_tree.heading('#0', text='پوشه')
        self.folders_tree.heading('Files', text='تعداد فایل')
        self.folders_tree.heading('Success', text='موفق')
        self.folders_tree.heading('Failed', text='ناموفق')
        self.folders_tree.heading('Classes', text='کلاس‌ها')
        self.folders_tree.heading('Functions', text='توابع')
        
        self.folders_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_code_tab(self):
        """ایجاد تب نمایش کد"""
        self.code_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.code_tab, text="🔍 نمایش کد")
        
        # فریم اصلی با split
        main_frame = ttk.Frame(self.code_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # لیست فایل‌ها
        list_frame = ttk.LabelFrame(main_frame, text="📄 فایل‌های پروژه")
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.file_listbox = tk.Listbox(list_frame, width=50, height=30)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # نمایش کد
        code_frame = ttk.LabelFrame(main_frame, text="📝 محتوای فایل")
        code_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD, width=80)
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # اتصال event
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
    
    def _create_log_tab(self):
        """ایجاد تب لاگ"""
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="📋 لاگ اسکن")
        
        self.log_display = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_display.config(state=tk.DISABLED)
    
    def browse_folder(self):
        """انتخاب پوشه پروژه"""
        folder_path = filedialog.askdirectory(title="پوشه پروژه را انتخاب کنید")
        if folder_path:
            self.path_var.set(folder_path)
            self.log(f"📁 پوشه پروژه انتخاب شد: {folder_path}")
    
    def start_scan(self):
        """شروع فرآیند اسکن"""
        project_path = self.path_var.get()
        if not project_path or not os.path.exists(project_path):
            messagebox.showerror("خطا", "لطفاً یک مسیر معتبر انتخاب کنید")
            return
        
        self.progress['value'] = 0
        self.status_var.set("🟡 در حال اسکن پروژه...")
        self.log("🚀 شروع اسکن هوشمند...")
        
        # پاکسازی نتایج قبلی
        self.clear_results()
        
        # اجرای اسکن در thread جداگانه
        import threading
        thread = threading.Thread(target=self._perform_scan, args=(project_path,))
        thread.daemon = True
        thread.start()
    
    def _perform_scan(self, project_path: str):
        """انجام اسکن در background"""
        try:
            self.project_data = self.scanner.scan_project(project_path)
            self.root.after(0, self._display_results)
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
    
    def _display_results(self):
        """نمایش نتایج اسکن"""
        self.progress['value'] = 100
        self.status_var.set("🟢 اسکن کامل شد!")
        
        self._show_summary()
        self._show_folders_details()
        self._populate_file_list()
        self._update_log_tab()
        
        self.log("✅ اسکن با موفقیت کامل شد!")
        self.log(f"📊 نرخ موفقیت: {self.project_data['scan_info'].get('success_rate', 0):.1f}%")
        
        # نمایش پیام موفقیت
        messagebox.showinfo("موفقیت", 
                          f"اسکن با موفقیت کامل شد!\n"
                          f"تعداد فایل‌ها: {self.project_data['project_stats']['total_files']}\n"
                          f"نرخ موفقیت: {self.project_data['scan_info'].get('success_rate', 0):.1f}%")
    
    def _show_summary(self):
        """نمایش خلاصه پروژه"""
        # پاکسازی درخت
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        # اطلاعات اسکن
        scan_info = self.project_data["scan_info"]
        self.summary_tree.insert('', 'end', text='📋 اطلاعات اسکن', values=('', ''))
        self.summary_tree.insert('', 'end', text='  شناسه اسکن', values=(scan_info['scan_id'], ''))
        self.summary_tree.insert('', 'end', text='  زمان اسکن', values=(scan_info['timestamp'], ''))
        self.summary_tree.insert('', 'end', text='  وضعیت', values=(scan_info.get('status', 'N/A'), '✅'))
        
        # آمار پروژه
        stats = self.project_data["project_stats"]
        self.summary_tree.insert('', 'end', text='📊 آمار پروژه', values=('', ''))
        self.summary_tree.insert('', 'end', text='  کل فایل‌ها', values=(stats['total_files'], ''))
        self.summary_tree.insert('', 'end', text='  فایل‌های تحلیل شده', values=(stats['analyzed_files'], '✅'))
        self.summary_tree.insert('', 'end', text='  فایل‌های موفق', values=(stats['successful_files'], '✅'))
        self.summary_tree.insert('', 'end', text='  فایل‌های ناموفق', values=(stats['failed_files'], '❌' if stats['failed_files'] > 0 else '✅'))
        
        # آنالیز کد
        analysis = self.project_data["code_analysis"]
        self.summary_tree.insert('', 'end', text='🔍 آنالیز کد', values=('', ''))
        self.summary_tree.insert('', 'end', text='  کلاس‌ها', values=(analysis['classes'], ''))
        self.summary_tree.insert('', 'end', text='  توابع', values=(analysis['functions'], ''))
        self.summary_tree.insert('', 'end', text='  متدها', values=(analysis['methods'], ''))
        self.summary_tree.insert('', 'end', text='  خطوط کد', values=(analysis['lines_of_code'], ''))
        self.summary_tree.insert('', 'end', text='  Docstringها', values=(analysis['docstrings'], ''))
        self.summary_tree.insert('', 'end', text='  کامنت‌ها', values=(analysis['comments'], ''))
    
    def _show_folders_details(self):
        """نمایش جزئیات پوشه‌ها"""
        # پاکسازی درخت
        for item in self.folders_tree.get_children():
            self.folders_tree.delete(item)
        
        for folder_name, folder_data in self.project_data["folders"].items():
            self.folders_tree.insert('', 'end', text=folder_name, 
                                   values=(folder_data['file_count'],
                                          folder_data['successful_files'],
                                          folder_data['failed_files'],
                                          folder_data['analysis']['classes'],
                                          folder_data['analysis']['functions']))
    
    def _populate_file_list(self):
        """پر کردن لیست فایل‌ها"""
        self.file_listbox.delete(0, tk.END)
        self.all_files = []
        
        for folder_name, folder_data in self.project_data["folders"].items():
            for file_data in folder_data["files"]:
                display_name = f"{folder_name}/{file_data['file_name']}"
                if "error" in file_data:
                    display_name = f"❌ {display_name}"
                else:
                    display_name = f"✅ {display_name}"
                
                self.all_files.append((display_name, file_data))
                self.file_listbox.insert(tk.END, display_name)
    
    def on_file_select(self, event):
        """هنگام انتخاب فایل از لیست"""
        selection = self.file_listbox.curselection()
        if selection and hasattr(self, 'all_files'):
            index = selection[0]
            display_name, file_data = self.all_files[index]
            
            self.code_text.config(state=tk.NORMAL)
            self.code_text.delete(1.0, tk.END)
            
            if "error" in file_data:
                content = f"❌ خطا در تحلیل فایل:\n"
                content += f"فایل: {file_data['file_name']}\n"
                content += f"خطا: {file_data['error']}\n"
                content += f"نوع خطا: {file_data.get('error_type', 'N/A')}\n"
            else:
                content = f"✅ فایل: {file_data['file_name']}\n"
                content += f"📁 مسیر: {file_data['file_path']}\n"
                content += f"📏 اندازه: {file_data['file_size']} بایت\n"
                content += f"📝 خطوط کد: {file_data['lines_of_code']}\n"
                content += f"🏗️  کلاس‌ها: {file_data.get('classes_count', 0)}\n"
                content += f"🔧 توابع: {file_data.get('functions_count', 0)}\n"
                content += f"🔄 متدها: {file_data.get('methods_count', 0)}\n"
                content += "=" * 60 + "\n\n"
                content += file_data.get('content_preview', 'محتوایی برای نمایش وجود ندارد')
            
            self.code_text.insert(tk.END, content)
            self.code_text.config(state=tk.DISABLED)
    
    def _update_log_tab(self):
        """به‌روزرسانی تب لاگ"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.delete(1.0, tk.END)
        
        content = "📋 گزارش کامل اسکن:\n"
        content += "=" * 50 + "\n\n"
        
        # اطلاعات کلی
        content += f"🆔 شناسه اسکن: {self.project_data['scan_info']['scan_id']}\n"
        content += f"🕒 زمان: {self.project_data['scan_info']['timestamp']}\n"
        content += f"📁 پروژه: {self.project_data['scan_info']['project_path']}\n"
        content += f"✅ وضعیت: {self.project_data['scan_info'].get('status', 'N/A')}\n\n"
        
        # فایل‌های هر پوشه
        for folder_name, folder_data in self.project_data["folders"].items():
            content += f"📁 {folder_name}:\n"
            content += f"   📄 فایل‌ها: {folder_data['file_count']}\n"
            content += f"   ✅ موفق: {folder_data['successful_files']}\n"
            content += f"   ❌ ناموفق: {folder_data['failed_files']}\n"
            
            # فایل‌های ناموفق
            failed_files = [f for f in folder_data['files'] if 'error' in f]
            if failed_files:
                content += "   ‼️ فایل‌های مشکل‌دار:\n"
                for file_data in failed_files[:3]:  # فقط 3 تای اول
                    content += f"      - {file_data['file_name']}: {file_data['error']}\n"
            content += "\n"
        
        self.log_display.insert(tk.END, content)
        self.log_display.config(state=tk.DISABLED)
    
    def export_report(self):
        """ذخیره گزارش"""
        if not self.project_data:
            messagebox.showwarning("هشدار", "هیچ گزارشی برای ذخیره‌سازی وجود ندارد")
            return
        
        # گزارش قبلاً ذخیره شده، فقط مسیر را نشان بده
        report_path = f"scan_reports/code_scan_report_{self.scanner.scan_id}.json"
        summary_path = f"scan_reports/scan_summary_{self.scanner.scan_id}.txt"
        
        messagebox.showinfo("گزارش ذخیره شد", 
                          f"گزارش‌ها با موفقیت ذخیره شدند:\n\n"
                          f"📄 گزارش کامل: {report_path}\n"
                          f"📝 گزارش خلاصه: {summary_path}")
    
    def clear_results(self):
        """پاکسازی نتایج"""
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        for item in self.folders_tree.get_children():
            self.folders_tree.delete(item)
        
        self.file_listbox.delete(0, tk.END)
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete(1.0, tk.END)
        self.code_text.config(state=tk.DISABLED)
        
        self.log_display.config(state=tk.NORMAL)
        self.log_display.delete(1.0, tk.END)
        self.log_display.config(state=tk.DISABLED)
        
        self.progress['value'] = 0
    
    def log(self, message: str):
        """ثبت پیام در کنسول لاگ"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def _show_error(self, error_msg: str):
        """نمایش خطا"""
        self.progress['value'] = 0
        self.status_var.set("🔴 خطا در اسکن")
        self.log(f"❌ خطا: {error_msg}")
        messagebox.showerror("خطا", f"خطا در اسکن پروژه:\n{error_msg}")


def main():
    """تابع اصلی"""
    root = tk.Tk()
    app = ScannerGUI_PRO(root)
    root.mainloop()


if __name__ == "__main__":
    main()