# i18n/locale_manager.py
import json
import os

class LocaleManager:
    def __init__(self, base_dir="locales", default_lang="fa"):
        self.base_dir = base_dir
        self.current_lang = default_lang
        self.strings = {}
        self.load_locale(self.current_lang)

    def locale_path(self, lang_code: str) -> str:
        return os.path.join(self.base_dir, lang_code, "ui_strings.json")

    def load_locale(self, lang_code: str):
        """بارگذاری فایل JSON زبان انتخابی."""
        path = self.locale_path(lang_code)
        self.strings = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.strings = json.load(f)
            except Exception:
                self.strings = {}
        self.current_lang = lang_code

    def get(self, key: str, fallback: str = "") -> str:
        return self.strings.get(key, fallback)

    def set_lang(self, lang_code: str):
        self.load_locale(lang_code)
