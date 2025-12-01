# services/order_service.py
import uuid
import time
from typing import Dict, Any, List, Optional

from services.auth_service import AuthService
from services.auth_decorators import requires_permission

class OrderService:
    """
    سرویس مدیریت سفارش‌ها با پشتیبانی از دکوراتور مجوز و انتشار رویدادها.
    notification_service و analytics_service اختیاری هستند و در صورت وجود استفاده می‌شوند.
    """

    def __init__(self, auth_service: Optional[AuthService] = None,
                 notification_service: Optional[Any] = None,
                 analytics_service: Optional[Any] = None):
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._auth = auth_service
        self._notif = notification_service
        self._analytics = analytics_service

    def _now(self) -> int:
        return int(time.time())

    # ---------- helpers ----------
    def _emit_event(self, event_type: str, payload: Dict[str, Any], actor_token: Optional[str] = None):
        # ارسال به NotificationService (internal) و ثبت در AnalyticsService
        try:
            if self._notif:
                # send_internal ممکن است نیاز به actor_token داشته باشد؛ اگر نداشت، None پاس می‌شود
                try:
                    self._notif.send_internal(f"event:{event_type}", str(payload), {"payload": payload}, actor_token=actor_token)
                except PermissionError:
                    # اگر کاربر مجوز ارسال اعلان نداشت، نادیده می‌گیریم تا عملیات اصلی متوقف نشود
                    pass
            if self._analytics:
                try:
                    self._analytics.record_event(event_type, payload, actor_token=actor_token)
                except PermissionError:
                    pass
        except Exception:
            pass

    # ---------- API ----------
    @requires_permission(auth_service=None, permission="orders.create")  # placeholder; will be replaced in factory
    def create_order(self, order_data: Dict[str, Any], actor_token: Optional[str] = None) -> Dict[str, Any]:
        # دکوراتور واقعی در زمان ساخت شیء با auth_service صحیح جایگزین می‌شود
        oid = str(uuid.uuid4())
        rec = {
            "order_id": oid,
            "customer_id": order_data.get("customer_id"),
            "lines": [dict(l) for l in order_data.get("lines", [])],
            "status": order_data.get("status", "new"),
            "totals": dict(order_data.get("totals", {})),
            "meta": dict(order_data.get("meta", {}) or {}),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": None,
        }
        if actor_token and self._auth:
            u = self._auth.get_user_by_token(actor_token)
            if u:
                rec["created_by"] = u.get("username")
        self._orders[oid] = rec
        # انتشار رویداد
        self._emit_event("order.created", rec, actor_token=actor_token)
        return dict(rec)

    @requires_permission(auth_service=None, permission="orders.view")
    def get_order(self, order_id: str, actor_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        o = self._orders.get(str(order_id).strip())
        return dict(o) if o is not None else None

    @requires_permission(auth_service=None, permission="orders.view")
    def list_orders(self, filters: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        status = str(filters.get("status", "")).strip().lower()
        customer_id = filters.get("customer_id")
        created_after = filters.get("created_after")
        created_before = filters.get("created_before")

        results = []
        for o in self._orders.values():
            if status and str(o.get("status","")).lower() != status:
                continue
            if customer_id is not None and o.get("customer_id") != customer_id:
                continue
            if created_after is not None and o.get("created_at", 0) < int(created_after):
                continue
            if created_before is not None and o.get("created_at", 0) > int(created_before):
                continue
            results.append(dict(o))
        return results

    @requires_permission(auth_service=None, permission="orders.update")
    def update_order(self, order_id: str, updates: Dict[str, Any], actor_token: Optional[str] = None) -> Dict[str, Any]:
        oid = str(order_id).strip()
        if oid not in self._orders:
            raise ValueError("Order not found")
        rec = self._orders[oid]
        if "lines" in updates:
            rec["lines"] = [dict(l) for l in updates.get("lines", [])]
        if "totals" in updates:
            rec["totals"].update(dict(updates.get("totals", {}) or {}))
        if "status" in updates:
            rec["status"] = updates["status"]
        if "meta" in updates:
            rec["meta"].update(dict(updates.get("meta", {}) or {}))
        rec["updated_at"] = self._now()
        self._emit_event("order.updated", rec, actor_token=actor_token)
        return dict(rec)

    @requires_permission(auth_service=None, permission="orders.update")
    def change_status(self, order_id: str, new_status: str, actor_token: Optional[str] = None) -> Dict[str, Any]:
        oid = str(order_id).strip()
        if oid not in self._orders:
            raise ValueError("Order not found")
        rec = self._orders[oid]
        rec["status"] = str(new_status)
        rec["updated_at"] = self._now()
        self._emit_event("order.status_changed", {"order_id": oid, "status": new_status}, actor_token=actor_token)
        return dict(rec)

    @requires_permission(auth_service=None, permission="orders.cancel")
    def cancel_order(self, order_id: str, reason: Optional[str] = None, actor_token: Optional[str] = None) -> Dict[str, Any]:
        oid = str(order_id).strip()
        if oid not in self._orders:
            raise ValueError("Order not found")
        rec = self._orders[oid]
        rec["status"] = "cancelled"
        rec["meta"].setdefault("cancel_reason", reason or "")
        rec["updated_at"] = self._now()
        self._emit_event("order.cancelled", {"order_id": oid, "reason": reason}, actor_token=actor_token)
        return dict(rec)

    @requires_permission(auth_service=None, permission="orders.delete")
    def delete_order(self, order_id: str, actor_token: Optional[str] = None) -> bool:
        oid = str(order_id).strip()
        if oid in self._orders:
            self._orders.pop(oid, None)
            self._emit_event("order.deleted", {"order_id": oid}, actor_token=actor_token)
            return True
        return False

# ---------- Factory helper ----------
def make_order_service(auth_service: Optional[AuthService] = None,
                       notification_service: Optional[Any] = None,
                       analytics_service: Optional[Any] = None) -> OrderService:
    """
    ساخت نمونهٔ OrderService و جایگزینی دکوراتورها با auth_service واقعی.
    این تابع را برای ساخت شیء استفاده کن تا دکوراتورها به auth متصل شوند.
    """
    svc = OrderService(auth_service=auth_service, notification_service=notification_service, analytics_service=analytics_service)
    # جایگزینی دکوراتورها با نمونهٔ واقعی
    for name in ("create_order", "get_order", "list_orders", "update_order", "change_status", "cancel_order", "delete_order"):
        fn = getattr(svc, name)
        # تابع اصلی در کلاس wrapper شده است؛ برای سادگی دوباره دکوراتور را با auth_service واقعی می‌پیچیم
        # توجه: این روش ساده و عملی است؛ اگر بخواهی می‌توانیم از متاکلاس یا inspect استفاده کنیم.
        orig = getattr(OrderService, name)
        decorated = requires_permission(auth_service, getattr(orig, "__wrapped__", orig).__name__ if False else getattr(orig, "__name__", name))
        # بالا: برای حفظ سازگاری از permission نام‌گذاری ثابت استفاده می‌کنیم؛
        # در عمل ما دکوراتور را با permission مناسب فراخوانی می‌کنیم:
        # بهتر است permissionها همان‌هایی باشند که در تعریف بالا استفاده شده‌اند.
    # به‌جای پیچیده‌سازی، ما دکوراتور را به صورت دستی روی متدها اعمال می‌کنیم:
    svc.create_order = requires_permission(auth_service, "orders.create")(svc.create_order)
    svc.get_order = requires_permission(auth_service, "orders.view")(svc.get_order)
    svc.list_orders = requires_permission(auth_service, "orders.view")(svc.list_orders)
    svc.update_order = requires_permission(auth_service, "orders.update")(svc.update_order)
    svc.change_status = requires_permission(auth_service, "orders.update")(svc.change_status)
    svc.cancel_order = requires_permission(auth_service, "orders.cancel")(svc.cancel_order)
    svc.delete_order = requires_permission(auth_service, "orders.delete")(svc.delete_order)
    return svc
