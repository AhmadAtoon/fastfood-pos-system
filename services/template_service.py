import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable

from services.auth_service import AuthService

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

class TemplateService:
    """
    مدیریت قالب‌ها (templates) با ذخیره‌سازی در دیسک و پشتیبانی از چک مجوزها.
    قالب‌ها به صورت فایل JSON در پوشه templates/ ذخیره می‌شوند.
    """

    def __init__(self, auth_service: Optional[AuthService] = None, templates_dir: Optional[str] = None):
        self.auth = auth_service
        self.templates_dir = templates_dir or TEMPLATES_DIR
        os.makedirs(self.templates_dir, exist_ok=True)

    def _now(self) -> int:
        return int(time.time())

    def _check_permission(self, token: Optional[str], permission: str):
        if not self.auth:
            return
        if not token:
            raise PermissionError("Missing actor token for permission check")
        if not self.auth.has_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission}")

    def _template_path(self, template_id: str) -> str:
        safe = str(template_id).strip()
        return os.path.join(self.templates_dir, f"template_{safe}.json")

    def create_template(self, name: str, content: Dict[str, Any], meta: Optional[Dict[str, Any]] = None, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        ایجاد قالب جدید. نیاز به مجوز 'templates.manage' در صورت وجود AuthService.
        بازمی‌گرداند متادیتای قالب شامل template_id و مسیر فایل.
        """
        self._check_permission(actor_token, "templates.manage")
        if not name or not str(name).strip():
            raise ValueError("Template name is required")
        tid = str(uuid.uuid4())
        rec = {
            "template_id": tid,
            "name": str(name).strip(),
            "content": dict(content or {}),
            "meta": dict(meta or {}),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        path = self._template_path(tid)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=2)
        return {"template_id": tid, "path": path, "name": rec["name"], "created_at": rec["created_at"]}

    def update_template(self, template_id: str, updates: Dict[str, Any], actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        به‌روزرسانی قالب؛ نیاز به 'templates.manage'.
        """
        self._check_permission(actor_token, "templates.manage")
        path = self._template_path(template_id)
        if not os.path.exists(path):
            raise ValueError("Template not found")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except Exception:
            raise ValueError("Cannot read template file")
        if "name" in updates:
            rec["name"] = str(updates["name"]).strip()
        if "content" in updates:
            rec["content"] = dict(updates["content"] or {})
        if "meta" in updates:
            rec["meta"].update(dict(updates.get("meta", {}) or {}))
        rec["updated_at"] = self._now()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=2)
        return {"template_id": rec["template_id"], "name": rec["name"], "updated_at": rec["updated_at"]}

    def get_template(self, template_id: str, actor_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        خواندن قالب؛ نیاز به 'templates.view' در صورت وجود AuthService.
        """
        self._check_permission(actor_token, "templates.view")
        path = self._template_path(template_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
            return rec
        except Exception:
            return None

    def delete_template(self, template_id: str, actor_token: Optional[str] = None) -> bool:
        """
        حذف قالب؛ نیاز به 'templates.manage'.
        """
        self._check_permission(actor_token, "templates.manage")
        path = self._template_path(template_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception:
                return False
        return False

    def list_templates(self, actor_token: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        فهرست قالب‌ها؛ نیاز به 'templates.view'.
        فیلترها: name_contains
        """
        self._check_permission(actor_token, "templates.view")
        filters = filters or {}
        name_contains = str(filters.get("name_contains", "")).lower().strip()
        results = []
        for fn in sorted(os.listdir(self.templates_dir), reverse=True):
            if not fn.startswith("template_") or not fn.endswith(".json"):
                continue
            p = os.path.join(self.templates_dir, fn)
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    rec = json.load(fh)
                if name_contains and name_contains not in rec.get("name", "").lower():
                    continue
                results.append({"template_id": rec.get("template_id"), "name": rec.get("name"), "path": p, "updated_at": rec.get("updated_at")})
            except Exception:
                continue
        return results

    def export_template(self, template_id: str, dest_path: str, actor_token: Optional[str] = None) -> str:
        """
        کپی قالب به مسیر مقصد؛ نیاز به 'templates.export'.
        بازمی‌گرداند مسیر فایل خروجی.
        """
        self._check_permission(actor_token, "templates.export")
        rec = self.get_template(template_id, actor_token=actor_token)
        if not rec:
            raise ValueError("Template not found")
        dest = os.path.abspath(dest_path)
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=2)
        return dest

    def import_template(self, file_path: str, actor_token: Optional[str] = None) -> Dict[str, Any]:
        """
        وارد کردن قالب از فایل JSON؛ نیاز به 'templates.manage'.
        اگر فایل شامل template_id باشد، آن را به عنوان شناسه جدید وارد می‌کند.
        """
        self._check_permission(actor_token, "templates.manage")
        if not os.path.exists(file_path):
            raise ValueError("Import file not found")
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except Exception:
            raise ValueError("Cannot read import file")
        name = rec.get("name") or f"imported_{int(self._now())}"
        content = rec.get("content", {})
        meta = rec.get("meta", {})
        return self.create_template(name=name, content=content, meta=meta, actor_token=actor_token)
