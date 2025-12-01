import uuid
import time
from typing import Dict, Any, List, Optional

class CustomerService:
    """
    سرویس مدیریت مشتریان (درون‌حافظه‌ای).
    رکورد مشتری:
    {
      "customer_id": str,
      "name": str,
      "phone": str,
      "email": str,
      "addresses": [ { "address_id": str, "label": str, "line1": str, "city": str, "postal_code": str, "meta": {} } ],
      "meta": {},
      "created_at": int,
      "updated_at": int
    }
    """

    def __init__(self):
        self._customers: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> int:
        return int(time.time())

    def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        email = str(data.get("email", "")).strip()
        if not name:
            raise ValueError("Customer name is required")
        cid = str(uuid.uuid4())
        rec = {
            "customer_id": cid,
            "name": name,
            "phone": phone,
            "email": email,
            "addresses": [],
            "meta": dict(data.get("meta", {}) or {}),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self._customers[cid] = rec
        return rec

    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        cid = str(customer_id).strip()
        if cid not in self._customers:
            raise ValueError("Customer not found")
        rec = self._customers[cid]
        # فقط فیلدهای مجاز را به‌روزرسانی می‌کنیم
        for k in ("name", "phone", "email"):
            if k in updates:
                rec[k] = str(updates[k]).strip()
        if "meta" in updates:
            rec["meta"].update(dict(updates.get("meta", {}) or {}))
        rec["updated_at"] = self._now()
        return rec

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self._customers.get(str(customer_id).strip())

    def delete_customer(self, customer_id: str) -> bool:
        cid = str(customer_id).strip()
        if cid in self._customers:
            self._customers.pop(cid, None)
            return True
        return False

    def list_customers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        name_contains = str(filters.get("name_contains", "")).lower().strip()
        phone = str(filters.get("phone", "")).strip()
        email_contains = str(filters.get("email_contains", "")).lower().strip()
        city = str(filters.get("city", "")).lower().strip()

        results = []
        for c in self._customers.values():
            if name_contains and name_contains not in c.get("name", "").lower():
                continue
            if phone and phone != c.get("phone", ""):
                continue
            if email_contains and email_contains not in c.get("email", "").lower():
                continue
            if city:
                # بررسی شهر در آدرس‌ها
                found_city = False
                for a in c.get("addresses", []):
                    if city in str(a.get("city", "")).lower():
                        found_city = True
                        break
                if not found_city:
                    continue
            results.append(c)
        return results

    def add_address(self, customer_id: str, address: Dict[str, Any]) -> Dict[str, Any]:
        cid = str(customer_id).strip()
        if cid not in self._customers:
            raise ValueError("Customer not found")
        addr_id = str(uuid.uuid4())
        rec_addr = {
            "address_id": addr_id,
            "label": str(address.get("label", "")).strip(),
            "line1": str(address.get("line1", "")).strip(),
            "city": str(address.get("city", "")).strip(),
            "postal_code": str(address.get("postal_code", "")).strip(),
            "meta": dict(address.get("meta", {}) or {}),
            "created_at": self._now(),
        }
        self._customers[cid]["addresses"].append(rec_addr)
        self._customers[cid]["updated_at"] = self._now()
        return rec_addr

    def remove_address(self, customer_id: str, address_id: str) -> bool:
        cid = str(customer_id).strip()
        if cid not in self._customers:
            raise ValueError("Customer not found")
        addrs = self._customers[cid].get("addresses", [])
        for i, a in enumerate(addrs):
            if a.get("address_id") == address_id:
                addrs.pop(i)
                self._customers[cid]["updated_at"] = self._now()
                return True
        return False

    def find_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        phone = str(phone).strip()
        for c in self._customers.values():
            if c.get("phone") == phone:
                return c
        return None
