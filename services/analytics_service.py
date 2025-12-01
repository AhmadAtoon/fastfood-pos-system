# services/analytics_service.py
import os
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict, Counter

from services.auth_service import AuthService

ANALYTICS_DIR = os.path.join(os.getcwd(), "analytics")
os.makedirs(ANALYTICS_DIR, exist_ok=True)

class AnalyticsService:
    """
    سرویس جمع‌آوری و خلاصه‌سازی رویدادها.
    - رویدادها به صورت دیکشنری ذخیره می‌شوند: {event_id, type, payload, ts}
    - متدهای خلاصه‌سازی پایه ارائه می‌شود.
    """

    def __init__(self, auth_service: Optional[AuthService] = None, storage_dir: Optional[str] = None):
        self.auth = auth_service
        self.storage_dir = storage_dir or ANALYTICS_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self._events: List[Dict[str, Any]] = []

    def _now(self) -> int:
        return int(time.time())

    def _check_permission(self, token: Optional[str], permission: str):
        if not self.auth:
            return
        if not token:
            raise PermissionError("Missing actor token for permission check")
        if not self.auth.has_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission}")

    def record_event(self, event_type: str, payload: Dict[str, Any], actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        ثبت یک رویداد. نیاز به 'analytics.manage' برای ثبت در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "analytics.manage")
        eid = f"evt_{int(self._now())}_{len(self._events)+1}"
        rec = {"event_id": eid, "type": event_type, "payload": dict(payload or {}), "ts": self._now()}
        self._events.append(rec)
        return dict(rec)

    def list_events(self, actor_token: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        فهرست رویدادها؛ نیاز به 'analytics.view'.
        """
        self._check_permission(actor_token, "analytics.view")
        return list(self._events[-limit:])

    def sales_by_day(self, actor_token: Optional[str] = None) -> Dict[str, float]:
        """
        خلاصه فروش بر اساس رویدادهای نوع 'order' یا 'payment' که شامل totals.grand_total هستند.
        نیاز به 'analytics.view'.
        """
        self._check_permission(actor_token, "analytics.view")
        by_day: Dict[str, float] = defaultdict(float)
        for e in self._events:
            if e.get("type") in ("order", "payment"):
                ts = int(e.get("ts", 0))
                day = time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else "unknown"
                amt = 0.0
                payload = e.get("payload", {})
                # تلاش برای یافتن مقدار فروش در چند مسیر ممکن
                if "totals" in payload and isinstance(payload["totals"], dict):
                    amt = float(payload["totals"].get("grand_total", 0) or 0)
                elif "amount" in payload:
                    amt = float(payload.get("amount", 0) or 0)
                by_day[day] += amt
        return dict(by_day)

    def orders_count_by_day(self, actor_token: Optional[str] = None) -> Dict[str, int]:
        self._check_permission(actor_token, "analytics.view")
        by_day: Dict[str, int] = defaultdict(int)
        for e in self._events:
            if e.get("type") == "order":
                ts = int(e.get("ts", 0))
                day = time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else "unknown"
                by_day[day] += 1
        return dict(by_day)

    def top_items(self, top_n: int = 10, actor_token: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        محاسبهٔ پرفروش‌ترین آیتم‌ها بر اساس رویدادهای order که شامل lines هستند.
        خروجی: لیست تاپ N به صورت (item_name_or_sku, qty)
        """
        self._check_permission(actor_token, "analytics.view")
        counter = Counter()
        for e in self._events:
            if e.get("type") == "order":
                payload = e.get("payload", {})
                lines = payload.get("lines", []) or []
                for ln in lines:
                    name = ln.get("name") or ln.get("sku") or "unknown"
                    qty = float(ln.get("qty", 0) or 0)
                    counter[name] += int(qty)
        return counter.most_common(top_n)

    def export_events(self, filename: str, actor_token: Optional[str] = None) -> str:
        """
        صادر کردن رویدادها به فایل JSON. نیاز به 'analytics.view'.
        """
        self._check_permission(actor_token, "analytics.view")
        path = os.path.abspath(filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._events, fh, ensure_ascii=False, indent=2)
        return path
