from typing import Dict, Any, List, Optional
import time

from services.auth_service import AuthService

class UserService:
    """
    سرویس مدیریت پروفایل کاربران.
    این نسخه از UserService:
    - از متدهای عمومی AuthService برای بررسی وجود کاربر استفاده می‌کند.
    - رکوردهای پروفایل را به صورت کپی بازمی‌گرداند تا مرجع داخلی لو نرود.
    - اعتبارسنجی پایه روی ورودی‌ها انجام می‌دهد.
    """

    def __init__(self, auth_service: Optional[AuthService] = None):
        self.auth = auth_service or AuthService()
        self._profiles: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> int:
        return int(time.time())

    def _user_exists_in_auth(self, username: str) -> bool:
        username = username.strip().lower()
        # استفاده از list_users برای جلوگیری از دسترسی مستقیم به فیلدهای خصوصی
        for u in self.auth.list_users():
            if u.get("username") == username:
                return True
        return False

    def create_profile(self, username: str, full_name: str, email: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        username = username.strip().lower()
        if not username:
            raise ValueError("username is required")
        if not full_name or not str(full_name).strip():
            raise ValueError("full_name is required")
        if not self._user_exists_in_auth(username):
            raise ValueError("User must be registered in AuthService first")
        if username in self._profiles:
            raise ValueError("Profile already exists")
        rec = {
            "username": username,
            "full_name": str(full_name).strip(),
            "email": str(email).strip(),
            "meta": dict(meta or {}),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        # ذخیره داخلی
        self._profiles[username] = rec
        # بازگرداندن کپی
        return dict(rec)

    def update_profile(self, username: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        username = username.strip().lower()
        if username not in self._profiles:
            raise ValueError("Profile not found")
        rec = self._profiles[username]
        # فقط فیلدهای مجاز را به‌روزرسانی می‌کنیم
        if "full_name" in updates:
            rec["full_name"] = str(updates["full_name"]).strip()
        if "email" in updates:
            rec["email"] = str(updates["email"]).strip()
        if "meta" in updates:
            rec["meta"].update(dict(updates.get("meta", {}) or {}))
        rec["updated_at"] = self._now()
        return dict(rec)

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        return dict(self._profiles.get(username.strip().lower())) if username and username.strip().lower() in self._profiles else None

    def delete_profile(self, username: str) -> bool:
        username = username.strip().lower()
        if username in self._profiles:
            self._profiles.pop(username, None)
            return True
        return False

    def list_profiles(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        name_contains = str(filters.get("name_contains", "")).lower().strip()
        email_contains = str(filters.get("email_contains", "")).lower().strip()
        results = []
        for p in self._profiles.values():
            if name_contains and name_contains not in p.get("full_name", "").lower():
                continue
            if email_contains and email_contains not in p.get("email", "").lower():
                continue
            results.append(dict(p))
        return results

    def assign_roles(self, username: str, roles: List[str]) -> Dict[str, Any]:
        username = username.strip().lower()
        if not self._user_exists_in_auth(username):
            raise ValueError("User not found in AuthService")
        # پیدا کردن رکورد کاربر از طریق list_users و به‌روزرسانی آن
        for u in self.auth.list_users():
            if u.get("username") == username:
                # AuthService.list_users بازنمایی بدون password برمی‌گرداند؛ برای به‌روزرسانی باید به _users دسترسی داشت
                # اگر AuthService متد عمومی برای assign role داشت از آن استفاده می‌کردیم.
                # در این پیاده‌سازی، اگر AuthService دارای attribute _users باشد از آن استفاده می‌کنیم با احتیاط.
                if hasattr(self.auth, "_users"):
                    internal = getattr(self.auth, "_users")
                    if username in internal:
                        current = set(internal[username].get("roles", []))
                        current.update([r.strip().lower() for r in roles])
                        internal[username]["roles"] = list(current)
                        internal[username]["updated_at"] = self._now()
                        return {k: v for k, v in internal[username].items() if k != "password"}
                # اگر دسترسی به _users ممکن نبود، خطا می‌دهیم
                raise RuntimeError("AuthService does not support role assignment via public API")
        raise ValueError("User not found in AuthService")

    def remove_roles(self, username: str, roles: List[str]) -> Dict[str, Any]:
        username = username.strip().lower()
        if not self._user_exists_in_auth(username):
            raise ValueError("User not found in AuthService")
        if hasattr(self.auth, "_users"):
            internal = getattr(self.auth, "_users")
            if username in internal:
                current = set(internal[username].get("roles", []))
                for r in roles:
                    current.discard(r.strip().lower())
                internal[username]["roles"] = list(current)
                internal[username]["updated_at"] = self._now()
                return {k: v for k, v in internal[username].items() if k != "password"}
        raise RuntimeError("AuthService does not support role removal via public API")
