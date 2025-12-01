# services/inventory_service.py
from typing import List, Dict, Any, Optional
import time

from services.auth_service import AuthService

class InventoryService:
    """
    سرویس مدیریت موجودی با پشتیبانی از چک مجوز در زمان اجرا.
    اگر نمونهٔ AuthService به سازنده پاس داده شود، متدهای حساس قبل از اجرا
    بررسی مجوز خواهند شد. پارامتر actor_token در متدها اختیاری است.
    همچنین امکان انتشار رویداد به notification_service و analytics_service وجود دارد.
    """

    def __init__(self, auth_service: Optional[AuthService] = None,
                 notification_service: Optional[Any] = None,
                 analytics_service: Optional[Any] = None):
        self._items: Dict[str, Dict[str, Any]] = {}
        self._transactions: List[Dict[str, Any]] = []
        self._reservations: Dict[str, List[Dict[str, Any]]] = {}
        self.auth = auth_service
        self._notif = notification_service
        self._analytics = analytics_service

    def _now(self) -> int:
        return int(time.time())

    def _check_permission(self, token: Optional[str], permission: str):
        """
        اگر auth service موجود باشد، بررسی می‌کند که token دارای permission است.
        در صورت عدم وجود token یا عدم مجوز، PermissionError پرتاب می‌شود.
        اگر auth service وجود نداشته باشد، چک نادیده گرفته می‌شود.
        """
        if not self.auth:
            return
        if not token:
            raise PermissionError("Missing actor token for permission check")
        if not self.auth.has_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission}")

    def _emit_event(self, event_type: str, payload: Dict[str, Any], actor_token: Optional[str] = None):
        """
        ارسال رویداد به notification و analytics در صورت وجود.
        خطاهای مجوز در ارسال رویداد نادیده گرفته می‌شوند تا عملیات اصلی متوقف نشود.
        """
        try:
            if self._notif:
                try:
                    self._notif.send_internal(f"event:{event_type}", str(payload), {"payload": payload}, actor_token=actor_token)
                except PermissionError:
                    pass
            if self._analytics:
                try:
                    self._analytics.record_event(event_type, payload, actor_token=actor_token)
                except PermissionError:
                    pass
        except Exception:
            pass

    # ---------- Item management ----------
    def upsert_item(self, sku: str, name: str, stock: float, price: float, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        item = {
            "sku": str(sku).strip(),
            "name": str(name).strip(),
            "stock": float(stock),
            "price": float(price),
            "meta": dict(meta or {}),
            "updated_at": self._now(),
        }
        self._items[item["sku"]] = item
        return dict(item)

    def get_item(self, sku: str) -> Optional[Dict[str, Any]]:
        it = self._items.get(str(sku).strip())
        return dict(it) if it is not None else None

    def list_items(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        name_contains = str(filters.get("name_contains", "")).lower().strip()
        min_stock = filters.get("min_stock")
        max_stock = filters.get("max_stock")

        results = []
        for it in self._items.values():
            if name_contains and name_contains not in it["name"].lower():
                continue
            if min_stock is not None and it["stock"] < float(min_stock):
                continue
            if max_stock is not None and it["stock"] > float(max_stock):
                continue
            results.append(dict(it))
        return results

    # ---------- Stock adjustments ----------
    def adjust_stock(self, sku: str, delta: float, reason: str, meta: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        تغییر موجودی به اندازه‌ی delta (مثبت یا منفی).
        اگر auth service موجود باشد، نیاز به مجوز 'inventory.adjust' دارد.
        """
        # بررسی مجوز در زمان اجرا
        self._check_permission(actor_token, "inventory.adjust")

        sku = str(sku).strip()
        if sku not in self._items:
            raise ValueError("Item not found")

        allow_negative = bool((meta or {}).get("allow_negative", False))
        new_stock = self._items[sku]["stock"] + float(delta)
        if not allow_negative and new_stock < 0:
            new_stock = 0.0

        self._items[sku]["stock"] = round(new_stock, 2)
        self._items[sku]["updated_at"] = self._now()

        tx = {
            "sku": sku,
            "delta": float(delta),
            "reason": str(reason),
            "meta": dict(meta or {}),
            "at": self._now(),
            "final_stock": self._items[sku]["stock"],
        }
        self._transactions.append(tx)
        self._emit_event("inventory.adjusted", tx, actor_token=actor_token)
        return dict(tx)

    def transactions(self) -> List[Dict[str, Any]]:
        """
        لیست تراکنش‌های موجودی (تاریخچه‌ی تغییرات).
        """
        return [dict(t) for t in self._transactions]

    # ---------- Reservations and order flow ----------
    def reserve_for_order(self, order_id: str, lines: List[Dict[str, Any]], actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        رزرو موجودی برای سفارش:
        - lines: [{"sku": "FOOD-001", "qty": 2.0}, ...]
        اگر auth service موجود باشد، نیاز به مجوز 'orders.reserve' دارد.
        رزروها به صورت موقت موجودی را کاهش می‌کنند.
        """
        self._check_permission(actor_token, "orders.reserve")

        order_id = str(order_id).strip()
        reservation = []

        # بررسی کفایت موجودی
        for ln in lines:
            sku = str(ln.get("sku", "")).strip()
            qty = float(ln.get("qty", 0.0))
            item = self.get_item(sku)
            if not item:
                raise ValueError(f"Item not found: {sku}")
            if item["stock"] < qty:
                raise ValueError(f"Insufficient stock for {sku}: need {qty}, have {item['stock']}")

        # اعمال رزرو (کاهش موقت)
        for ln in lines:
            sku = str(ln.get("sku", "")).strip()
            qty = float(ln.get("qty", 0.0))
            self._items[sku]["stock"] = round(self._items[sku]["stock"] - qty, 2)
            self._items[sku]["updated_at"] = self._now()
            reservation.append({"sku": sku, "qty": qty})

        self._reservations[order_id] = reservation
        res = {"order_id": order_id, "reserved": [dict(r) for r in reservation], "reserved_at": self._now()}
        self._emit_event("inventory.reserved", res, actor_token=actor_token)
        return res

    def release_order(self, order_id: str, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        آزادسازی رزروهای سفارش و بازگرداندن موجودی.
        اگر auth service موجود باشد، نیاز به مجوز 'orders.release' دارد.
        """
        self._check_permission(actor_token, "orders.release")

        order_id = str(order_id).strip()
        reservation = self._reservations.get(order_id)
        if not reservation:
            return {"order_id": order_id, "released": [], "released_at": self._now()}

        for r in reservation:
            sku = r["sku"]; qty = float(r["qty"])
            self._items[sku]["stock"] = round(self._items[sku]["stock"] + qty, 2)
            self._items[sku]["updated_at"] = self._now()

        self._reservations.pop(order_id, None)
        res = {"order_id": order_id, "released": [dict(r) for r in reservation], "released_at": self._now()}
        self._emit_event("inventory.released", res, actor_token=actor_token)
        return res

    def commit_order(self, order_id: str, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        تأیید رزروها و ثبت تراکنش‌های کاهش قطعی موجودی.
        اگر auth service موجود باشد، نیاز به مجوز 'orders.commit' دارد.
        """
        self._check_permission(actor_token, "orders.commit")

        order_id = str(order_id).strip()
        reservation = self._reservations.get(order_id)
        if not reservation:
            return {"order_id": order_id, "committed": [], "committed_at": self._now()}

        committed = []
        for r in reservation:
            sku = r["sku"]; qty = float(r["qty"])
            tx = {
                "sku": sku,
                "delta": 0.0,
                "reason": f"commit:{order_id}",
                "meta": {"reserved_qty": qty},
                "at": self._now(),
                "final_stock": self._items[sku]["stock"],
            }
            self._transactions.append(tx)
            committed.append({**r, "final_stock": tx["final_stock"]})

        self._reservations.pop(order_id, None)
        res = {"order_id": order_id, "committed": committed, "committed_at": self._now()}
        self._emit_event("inventory.committed", res, actor_token=actor_token)
        return res
