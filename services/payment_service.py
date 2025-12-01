# services/payment_service.py
import uuid
import time
from typing import Dict, Any, List, Optional

from services.auth_service import AuthService
from services.auth_decorators import requires_permission

class PaymentService:
    def __init__(self, auth_service: Optional[AuthService] = None,
                 notification_service: Optional[Any] = None,
                 analytics_service: Optional[Any] = None):
        self._auth = auth_service
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._notif = notification_service
        self._analytics = analytics_service

    def _now(self) -> int:
        return int(time.time())

    def _emit_event(self, event_type: str, payload: Dict[str, Any], actor_token: Optional[str] = None):
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

    @requires_permission(auth_service=None, permission="payments.process")
    def process_payment(self, order_id: Optional[str], amount: float, currency: str = "IRR",
                        provider: str = "simulated", meta: Optional[Dict[str, Any]] = None,
                        actor_token: Optional[str] = None) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("amount must be positive")
        tx_id = str(uuid.uuid4())
        rec = {
            "tx_id": tx_id,
            "order_id": order_id,
            "type": "charge",
            "amount": float(amount),
            "currency": str(currency),
            "status": "success",
            "provider": str(provider),
            "meta": dict(meta or {}),
            "created_at": self._now(),
            "related_tx": None
        }
        self._transactions[tx_id] = rec
        self._emit_event("payment.processed", rec, actor_token=actor_token)
        return dict(rec)

    @requires_permission(auth_service=None, permission="payments.refund")
    def refund_payment(self, tx_id: str, amount: Optional[float] = None, reason: Optional[str] = None,
                       actor_token: Optional[str] = None) -> Dict[str, Any]:
        orig = self._transactions.get(str(tx_id).strip())
        if not orig:
            raise ValueError("Original transaction not found")
        if orig.get("type") != "charge":
            raise ValueError("Can only refund charge transactions")
        if orig.get("status") != "success":
            raise ValueError("Original transaction not successful")

        refund_amount = float(amount) if amount is not None else float(orig.get("amount", 0.0))
        if refund_amount <= 0:
            raise ValueError("refund amount must be positive")
        if refund_amount > float(orig.get("amount", 0.0)):
            raise ValueError("refund amount exceeds original amount")

        refund_id = str(uuid.uuid4())
        rec = {
            "tx_id": refund_id,
            "order_id": orig.get("order_id"),
            "type": "refund",
            "amount": refund_amount,
            "currency": orig.get("currency"),
            "status": "refunded",
            "provider": orig.get("provider"),
            "meta": {"reason": reason or "", "original_tx": tx_id},
            "created_at": self._now(),
            "related_tx": tx_id
        }
        self._transactions[refund_id] = rec
        if abs(refund_amount - float(orig.get("amount", 0.0))) < 1e-6:
            orig["status"] = "refunded"
        else:
            orig_meta = orig.setdefault("meta", {})
            refunded_total = orig_meta.get("refunded_total", 0.0) + refund_amount
            orig_meta["refunded_total"] = refunded_total
        self._emit_event("payment.refunded", rec, actor_token=actor_token)
        return dict(rec)

    @requires_permission(auth_service=None, permission="payments.view")
    def get_transaction(self, tx_id: str, actor_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        t = self._transactions.get(str(tx_id).strip())
        return dict(t) if t is not None else None

    @requires_permission(auth_service=None, permission="payments.view")
    def list_transactions(self, filters: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        order_id = filters.get("order_id")
        tx_type = filters.get("type")
        provider = filters.get("provider")
        status = filters.get("status")
        min_amount = filters.get("min_amount")
        max_amount = filters.get("max_amount")

        results = []
        for t in self._transactions.values():
            if order_id is not None and t.get("order_id") != order_id:
                continue
            if tx_type is not None and t.get("type") != tx_type:
                continue
            if provider is not None and t.get("provider") != provider:
                continue
            if status is not None and t.get("status") != status:
                continue
            if min_amount is not None and float(t.get("amount", 0.0)) < float(min_amount):
                continue
            if max_amount is not None and float(t.get("amount", 0.0)) > float(max_amount):
                continue
            results.append(dict(t))
        return results

# Factory
def make_payment_service(auth_service: Optional[AuthService] = None,
                         notification_service: Optional[Any] = None,
                         analytics_service: Optional[Any] = None) -> PaymentService:
    svc = PaymentService(auth_service=auth_service, notification_service=notification_service, analytics_service=analytics_service)
    svc.process_payment = requires_permission(auth_service, "payments.process")(svc.process_payment)
    svc.refund_payment = requires_permission(auth_service, "payments.refund")(svc.refund_payment)
    svc.get_transaction = requires_permission(auth_service, "payments.view")(svc.get_transaction)
    svc.list_transactions = requires_permission(auth_service, "payments.view")(svc.list_transactions)
    return svc
