import os
import json
import csv
import time
import uuid
from typing import Callable, Dict, Any, Optional, List

from services.auth_service import AuthService

REPORTS_DIR = os.path.join(os.getcwd(), "reports_cache")
os.makedirs(REPORTS_DIR, exist_ok=True)

class ReportingService:
    """
    سرویس تولید و صادرسازی گزارش‌ها با پشتیبانی از providers و چک مجوزها.
    - providers: name -> callable() -> dict (داده‌های خام برای گزارش)
    - گزارش‌های تولیدشده در حافظه و به صورت فایل JSON در reports_cache ذخیره می‌شوند.
    """

    def __init__(self, auth_service: Optional[AuthService] = None, cache_dir: Optional[str] = None):
        self.auth = auth_service
        self._providers: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._cache_dir = cache_dir or REPORTS_DIR
        os.makedirs(self._cache_dir, exist_ok=True)
        self._cache_index: Dict[str, Dict[str, Any]] = {}  # report_id -> meta

    # ---------- Provider management ----------
    def register_data_provider(self, name: str, provider: Callable[[], Dict[str, Any]]) -> None:
        if not callable(provider):
            raise ValueError("provider must be callable")
        self._providers[str(name)] = provider

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    # ---------- Permission helper ----------
    def _check_permission(self, token: Optional[str], permission: str):
        if not self.auth:
            return
        if not token:
            raise PermissionError("Missing actor token for permission check")
        if not self.auth.has_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission}")

    # ---------- Report generation ----------
    def list_report_types(self) -> List[str]:
        return ["sales_summary", "inventory_status", "orders_by_customer"]

    def generate_report(self, report_type: str, params: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        تولید گزارش بر اساس report_type و params.
        خروجی: {report_id, type, generated_at, params, data}
        نیاز به مجوز 'reports.view' در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "reports.view")
        params = params or {}
        report_id = str(uuid.uuid4())
        generated_at = int(time.time())

        # جمع‌آوری داده‌ها از providers ثبت‌شده
        data_bundle: Dict[str, Any] = {}
        for name, prov in self._providers.items():
            try:
                data_bundle[name] = prov() or {}
            except Exception as e:
                data_bundle[name] = {"_error": str(e)}

        # تولید گزارش‌های نمونه بر اساس نوع
        if report_type == "sales_summary":
            # انتظار داریم provider orders وجود داشته باشد
            orders = data_bundle.get("orders", {}).get("orders", []) if isinstance(data_bundle.get("orders"), dict) else []
            total_sales = 0.0
            count = 0
            by_day: Dict[str, float] = {}
            for o in orders:
                amt = float(o.get("totals", {}).get("grand_total", 0) or 0)
                ts = int(o.get("created_at", 0) or 0)
                day = time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else "unknown"
                by_day[day] = by_day.get(day, 0.0) + amt
                total_sales += amt
                count += 1
            report_data = {"total_sales": total_sales, "orders_count": count, "by_day": by_day}

        elif report_type == "inventory_status":
            items = data_bundle.get("inventory", {}).get("items", []) if isinstance(data_bundle.get("inventory"), dict) else []
            low_stock = []
            for it in items:
                try:
                    stock = float(it.get("stock", 0) or 0)
                except Exception:
                    stock = 0.0
                if stock <= float(params.get("threshold", 5)):
                    low_stock.append({"sku": it.get("sku"), "name": it.get("name"), "stock": stock})
            report_data = {"total_items": len(items), "low_stock": low_stock}

        elif report_type == "orders_by_customer":
            orders = data_bundle.get("orders", {}).get("orders", []) if isinstance(data_bundle.get("orders"), dict) else []
            by_customer: Dict[str, Dict[str, Any]] = {}
            for o in orders:
                cid = str(o.get("customer_id", "anonymous"))
                amt = float(o.get("totals", {}).get("grand_total", 0) or 0)
                rec = by_customer.setdefault(cid, {"customer_id": cid, "orders": 0, "total": 0.0})
                rec["orders"] += 1
                rec["total"] += amt
            report_data = {"customers": list(by_customer.values())}

        else:
            raise ValueError("Unknown report type")

        payload = {
            "report_id": report_id,
            "type": report_type,
            "generated_at": generated_at,
            "params": params,
            "data": report_data
        }

        # ذخیره در کش به صورت فایل JSON
        filename = f"report_{generated_at}_{report_id}.json"
        path = os.path.join(self._cache_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

        self._cache_index[report_id] = {"file": filename, "path": path, "meta": {"type": report_type, "generated_at": generated_at}}
        return dict(payload)

    # ---------- Cache management ----------
    def get_cached_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        meta = self._cache_index.get(report_id)
        if not meta:
            # تلاش برای یافتن در دایرکتوری
            for fn in os.listdir(self._cache_dir):
                if report_id in fn:
                    p = os.path.join(self._cache_dir, fn)
                    try:
                        with open(p, "r", encoding="utf-8") as fh:
                            return json.load(fh)
                    except Exception:
                        return None
            return None
        try:
            with open(meta["path"], "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def delete_cached_report(self, report_id: str) -> bool:
        meta = self._cache_index.get(report_id)
        if meta:
            try:
                os.remove(meta["path"])
            except Exception:
                pass
            self._cache_index.pop(report_id, None)
            return True
        # تلاش برای حذف فایل بر اساس نام
        for fn in os.listdir(self._cache_dir):
            if report_id in fn:
                try:
                    os.remove(os.path.join(self._cache_dir, fn))
                    return True
                except Exception:
                    return False
        return False

    # ---------- Export ----------
    def export_report(self, report_payload: Dict[str, Any], format: str, filename: str, actor_token: Optional[str] = None) -> str:
        """
        صادر کردن گزارش به فرمت json یا csv.
        نیاز به مجوز 'reports.export' در صورت وجود AuthService.
        بازمی‌گرداند مسیر فایل خروجی.
        """
        self._check_permission(actor_token, "reports.export")
        fmt = str(format or "json").lower()
        if fmt == "json":
            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(report_payload, fh, ensure_ascii=False, indent=2)
            return filename
        elif fmt == "csv":
            # برای csv سعی می‌کنیم داده‌ها را به صورت جدول ساده صادر کنیم
            data = report_payload.get("data", {})
            # حالت‌های شناخته‌شده را پشتیبانی می‌کنیم
            if "by_day" in data:
                # sales_summary by_day
                rows = [("day", "sales")]
                for day, amt in data["by_day"].items():
                    rows.append((day, amt))
                with open(filename, "w", newline='', encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerows(rows)
                return filename
            if "low_stock" in data:
                rows = [("sku", "name", "stock")]
                for it in data["low_stock"]:
                    rows.append((it.get("sku"), it.get("name"), it.get("stock")))
                with open(filename, "w", newline='', encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerows(rows)
                return filename
            if "customers" in data:
                rows = [("customer_id", "orders", "total")]
                for c in data["customers"]:
                    rows.append((c.get("customer_id"), c.get("orders"), c.get("total")))
                with open(filename, "w", newline='', encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerows(rows)
                return filename
            # fallback: dump JSON into CSV single column
            with open(filename, "w", newline='', encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["payload"])
                writer.writerow([json.dumps(report_payload.get("data", {}), ensure_ascii=False)])
            return filename
        else:
            raise ValueError("Unsupported export format")
