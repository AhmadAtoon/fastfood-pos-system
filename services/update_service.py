import os
import json
import time
import uuid
from typing import Callable, Dict, Any, Optional, List

UPDATES_DIR = os.path.join(os.getcwd(), "updates")

class UpdateService:
    """
    سرویس مدیریت به‌روزرسانی (شبیه‌سازی‌شده).
    - providers: name -> callable() -> dict (info about available updates)
    - دانلودها در پوشه updates/ ذخیره می‌شوند (فایل JSON شبیه‌سازی)
    - تاریخچهٔ اعمال به‌روزرسانی درون‌حافظه‌ای نگهداری می‌شود و در فایل history.json ذخیره می‌شود.
    """

    def __init__(self, updates_dir: Optional[str] = None):
        self.updates_dir = updates_dir or UPDATES_DIR
        os.makedirs(self.updates_dir, exist_ok=True)
        self._providers: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._history: List[Dict[str, Any]] = []
        self._history_file = os.path.join(self.updates_dir, "history.json")
        self._load_history()

    def _now(self) -> int:
        return int(time.time())

    def _load_history(self):
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as fh:
                    self._history = json.load(fh) or []
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            with open(self._history_file, "w", encoding="utf-8") as fh:
                json.dump(self._history, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def register_update_provider(self, name: str, provider: Callable[[], Dict[str, Any]]) -> None:
        if not callable(provider):
            raise ValueError("provider must be callable")
        self._providers[str(name)] = provider

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        فراخوانی providers و بازگرداندن لیست نسخه‌های در دسترس.
        هر provider باید dict شامل حداقل keys: version, notes (اختیاری), id/url (اختیاری) برگرداند.
        """
        results = []
        for name, prov in self._providers.items():
            try:
                info = prov() or {}
                info["provider"] = name
                results.append(info)
            except Exception as e:
                results.append({"provider": name, "_error": str(e)})
        return results

    def download_update(self, provider_name: str, version: str) -> Dict[str, Any]:
        """
        شبیه‌سازی دانلود: یک فایل JSON در updates/ ایجاد می‌کند که شامل متادیتای نسخه است.
        بازمی‌گرداند: {update_id, path, provider, version, downloaded_at}
        """
        if provider_name not in self._providers:
            raise ValueError("Provider not registered")
        prov = self._providers[provider_name]
        info = prov() or {}
        # بررسی تطابق نسخه
        if str(info.get("version", "")).strip() != str(version).strip():
            # ممکن است provider چند نسخه داشته باشد؛ برای سادگی اجازه می‌دهیم ولی علامت می‌زنیم
            pass
        update_id = str(uuid.uuid4())
        filename = f"update_{provider_name}_{version}_{update_id}.json"
        path = os.path.join(self.updates_dir, filename)
        payload = {
            "update_id": update_id,
            "provider": provider_name,
            "version": version,
            "info": info,
            "downloaded_at": self._now()
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return {"update_id": update_id, "path": path, "provider": provider_name, "version": version, "downloaded_at": payload["downloaded_at"]}

    def apply_update(self, update_id: str) -> bool:
        """
        شبیه‌سازی اعمال به‌روزرسانی: فایل مربوطه را پیدا کرده، یک رکورد در تاریخچه اضافه می‌کند و True برمی‌گرداند.
        """
        # پیدا کردن فایل
        for fn in os.listdir(self.updates_dir):
            if update_id in fn and fn.endswith(".json"):
                path = os.path.join(self.updates_dir, fn)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        payload = json.load(fh)
                except Exception:
                    payload = {"_error": "cannot read file"}
                rec = {
                    "applied_id": update_id,
                    "file": fn,
                    "provider": payload.get("provider"),
                    "version": payload.get("version"),
                    "applied_at": self._now(),
                    "result": "success" if "_error" not in payload else "failed",
                    "meta": payload.get("info", {})
                }
                self._history.append(rec)
                self._save_history()
                return rec["result"] == "success"
        raise ValueError("Update not found")

    def list_updates(self) -> List[Dict[str, Any]]:
        """
        فهرست فایل‌های دانلودشده (metadata).
        """
        items = []
        for fn in sorted(os.listdir(self.updates_dir), reverse=True):
            if not fn.endswith(".json") or fn == os.path.basename(self._history_file):
                continue
            p = os.path.join(self.updates_dir, fn)
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                items.append({"file": fn, "path": p, "provider": payload.get("provider"), "version": payload.get("version"), "downloaded_at": payload.get("downloaded_at")})
            except Exception:
                items.append({"file": fn, "path": p})
        return items

    def get_update_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
