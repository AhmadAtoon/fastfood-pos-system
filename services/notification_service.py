# services/notification_service.py
import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable

from services.auth_service import AuthService

NOTIF_DIR = os.path.join(os.getcwd(), "notifications")
os.makedirs(NOTIF_DIR, exist_ok=True)

class NotificationService:
    """
    سرویس اعلان ساده و شبیه‌سازی‌شده.
    - لاگ اعلان‌ها در پوشه notifications/ ذخیره می‌شود.
    - وبهوک‌ها با نوشتن فایل شبیه‌سازی می‌شوند.
    - امکان صف‌بندی و پردازش دستی queue وجود دارد.
    """

    def __init__(self, auth_service: Optional[AuthService] = None, storage_dir: Optional[str] = None):
        self.auth = auth_service
        self.storage_dir = storage_dir or NOTIF_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self._queue: List[Dict[str, Any]] = []
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._history_file = os.path.join(self.storage_dir, "history.json")
        self._load_history()

    def _now(self) -> int:
        return int(time.time())

    def _load_history(self):
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as fh:
                    self._history = json.load(fh) or []
            else:
                self._history = []
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            with open(self._history_file, "w", encoding="utf-8") as fh:
                json.dump(self._history, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _check_permission(self, token: Optional[str], permission: str):
        if not self.auth:
            return
        if not token:
            raise PermissionError("Missing actor token for permission check")
        if not self.auth.has_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission}")

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        ثبت listener که هنگام انتشار اعلان فراخوانی می‌شود.
        callback باید یک دیکشنری event بگیرد.
        """
        if callable(callback):
            self._listeners.append(callback)

    def send_internal(self, title: str, body: str, meta: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        ارسال اعلان داخلی: ذخیره در history و فراخوانی listenerها.
        نیاز به مجوز 'notify.send' در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "notify.send")
        nid = str(uuid.uuid4())
        rec = {
            "id": nid,
            "type": "internal",
            "title": str(title),
            "body": str(body),
            "meta": dict(meta or {}),
            "created_at": self._now()
        }
        self._history.append(rec)
        self._save_history()
        # فراخوانی listenerها
        for cb in list(self._listeners):
            try:
                cb(dict(rec))
            except Exception:
                pass
        return dict(rec)

    def send_webhook(self, url: str, payload: Dict[str, Any], actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        شبیه‌سازی ارسال وبهوک: نوشتن payload در فایل با نام مشتق از uuid.
        نیاز به مجوز 'notify.send' در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "notify.send")
        wid = str(uuid.uuid4())
        filename = f"webhook_{int(self._now())}_{wid}.json"
        path = os.path.join(self.storage_dir, filename)
        rec = {
            "id": wid,
            "type": "webhook",
            "url": url,
            "payload": payload,
            "file": filename,
            "created_at": self._now()
        }
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(rec, fh, ensure_ascii=False, indent=2)
        except Exception:
            raise IOError("Failed to write webhook file")
        self._history.append(rec)
        self._save_history()
        for cb in list(self._listeners):
            try:
                cb(dict(rec))
            except Exception:
                pass
        return dict(rec)

    def queue_notification(self, notif: Dict[str, Any]) -> str:
        """
        افزودن اعلان به صف برای پردازش بعدی.
        بازمی‌گرداند id صف.
        """
        qid = str(uuid.uuid4())
        item = {"queue_id": qid, "notif": notif, "enqueued_at": self._now()}
        self._queue.append(item)
        return qid

    def process_queue(self, actor_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        پردازش همهٔ آیتم‌های صف: هر آیتم را به عنوان internal ارسال می‌کند.
        نیاز به مجوز 'notify.manage' برای پردازش صف در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "notify.manage")
        processed = []
        while self._queue:
            item = self._queue.pop(0)
            notif = item.get("notif", {})
            try:
                rec = self.send_internal(notif.get("title", "queued"), notif.get("body", ""), notif.get("meta", {}), actor_token=actor_token)
                processed.append(rec)
            except Exception as e:
                # در صورت خطا، می‌توانیم آیتم را دوباره به صف اضافه کنیم یا لاگ کنیم
                processed.append({"error": str(e), "queue_id": item.get("queue_id")})
        return processed

    def list_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        فهرست تاریخچه اعلان‌ها.
        """
        return list(self._history[-limit:])

    def clear_history(self, actor_token: Optional[str] = None) -> bool:
        """
        پاک کردن تاریخچه؛ نیاز به 'notify.manage'.
        """
        self._check_permission(actor_token, "notify.manage")
        self._history = []
        self._save_history()
        return True
