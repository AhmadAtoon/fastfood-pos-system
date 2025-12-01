import os
import json
import time
import uuid
from typing import Callable, Dict, Any, Optional, List

BACKUP_DIR = os.path.join(os.getcwd(), "backups")

class BackupService:
    """
    سرویس پشتیبان‌گیری ساده و ماژولار.
    - providers: dict[name -> callable() -> dict] برای گرفتن داده‌ها
    - فایل‌های پشتیبان به صورت JSON در پوشه backups/ ذخیره می‌شوند.
    """

    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = backup_dir or BACKUP_DIR
        os.makedirs(self.backup_dir, exist_ok=True)
        self._providers: Dict[str, Callable[[], Dict[str, Any]]] = {}

    def register_provider(self, name: str, provider: Callable[[], Dict[str, Any]]) -> None:
        """
        ثبت provider با نام یکتا. provider باید بدون پارامتر اجرا شود و dict برگرداند.
        """
        if not callable(provider):
            raise ValueError("provider must be callable")
        self._providers[str(name)] = provider

    def create_backup(self, label: Optional[str] = None) -> Dict[str, Any]:
        """
        گرفتن snapshot از همه providers و ذخیره به عنوان فایل JSON.
        بازگشت متادیتا شامل backup_id و path.
        """
        if not self._providers:
            raise RuntimeError("No providers registered")

        snapshot = {}
        for name, prov in self._providers.items():
            try:
                snapshot[name] = prov() or {}
            except Exception as e:
                # ثبت خطا در snapshot به جای شکست کامل
                snapshot[name] = {"_error": str(e)}

        backup_id = str(uuid.uuid4())
        created_at = int(time.time())
        filename = f"backup_{created_at}_{backup_id}.json"
        path = os.path.join(self.backup_dir, filename)
        meta = {
            "backup_id": backup_id,
            "created_at": created_at,
            "label": label or "",
            "providers": list(self._providers.keys()),
            "file": filename
        }
        payload = {"meta": meta, "data": snapshot}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return {"backup_id": backup_id, "path": path, "created_at": created_at, "label": label or ""}

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        فهرست فایل‌های پشتیبان و متادیتای آن‌ها.
        """
        items = []
        for fn in sorted(os.listdir(self.backup_dir), reverse=True):
            if not fn.lower().endswith(".json"):
                continue
            p = os.path.join(self.backup_dir, fn)
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                meta = payload.get("meta", {})
            except Exception:
                meta = {"file": fn}
            items.append({"file": fn, "path": p, "meta": meta})
        return items

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        خواندن محتوای پشتیبان بر اساس backup_id.
        """
        for item in self.list_backups():
            meta = item.get("meta", {})
            if meta.get("backup_id") == backup_id or item["file"].find(backup_id) != -1:
                try:
                    with open(item["path"], "r", encoding="utf-8") as fh:
                        return json.load(fh)
                except Exception:
                    return None
        return None

    def restore_backup(self, backup_id: str, restore_callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        بازیابی: برای هر provider در backup، restore_callback(provider_name, data) را صدا می‌زند.
        restore_callback مسئول اعمال داده در سرویس مربوطه است.
        """
        payload = self.get_backup(backup_id)
        if not payload:
            raise ValueError("Backup not found")
        data = payload.get("data", {})
        for provider_name, provider_data in data.items():
            # اگر provider_data شامل خطا باشد، آن را نادیده می‌گیریم یا به callback می‌دهیم
            restore_callback(provider_name, provider_data)

    def delete_backup(self, backup_id: str) -> bool:
        """
        حذف فایل پشتیبان بر اساس backup_id.
        """
        for item in self.list_backups():
            meta = item.get("meta", {})
            if meta.get("backup_id") == backup_id or item["file"].find(backup_id) != -1:
                try:
                    os.remove(item["path"])
                    return True
                except Exception:
                    return False
        return False

    def verify_backup(self, backup_id: str) -> bool:
        """
        بررسی ساختار پشتیبان: وجود meta و data و اینکه providers در meta با data همخوانی دارند.
        """
        payload = self.get_backup(backup_id)
        if not payload:
            return False
        if "meta" not in payload or "data" not in payload:
            return False
        meta = payload["meta"]
        data = payload["data"]
        provs = meta.get("providers", [])
        # حداقل بررسی: همه provider names در data وجود داشته باشند
        for p in provs:
            if p not in data:
                return False
        return True

    def export_backup(self, backup_id: str, dest_path: str) -> str:
        """
        کپی فایل پشتیبان به مسیر مقصد و بازگرداندن مسیر جدید.
        """
        payload = self.get_backup(backup_id)
        if not payload:
            raise ValueError("Backup not found")
        # پیدا کردن فایل اصلی
        for item in self.list_backups():
            meta = item.get("meta", {})
            if meta.get("backup_id") == backup_id or item["file"].find(backup_id) != -1:
                dest = os.path.abspath(dest_path)
                with open(item["path"], "rb") as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                return dest
        raise ValueError("Backup file not found")

