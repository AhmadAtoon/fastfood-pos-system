import uuid
import time
import hashlib
from typing import Dict, Any, List, Optional

def _hash_password(password: str, salt: Optional[str] = None) -> str:
    s = salt or uuid.uuid4().hex
    h = hashlib.sha256((s + password).encode("utf-8")).hexdigest()
    return f"{s}${h}"

def _verify_password(stored: str, password: str) -> bool:
    try:
        s, h = stored.split("$", 1)
        return hashlib.sha256((s + password).encode("utf-8")).hexdigest() == h
    except Exception:
        return False

class AuthService:
    """
    سرویس احراز هویت و مجوزها (درون‌حافظه‌ای).
    - _users: username -> record (شامل roles)
    - _tokens: token -> {"username", "issued_at"}
    - _role_permissions: role -> [permission strings]
    """

    def __init__(self):
        self._users: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._role_permissions: Dict[str, List[str]] = {}

        # پیکربندی پیش‌فرض نقش‌ها (قابل تغییر با set_role_permissions)
        self._role_permissions.setdefault("admin", [
            "users.manage", "orders.create", "orders.update", "orders.view",
            "inventory.adjust", "inventory.view", "reports.export", "print.any"
        ])
        self._role_permissions.setdefault("manager", [
            "orders.view", "reports.export", "inventory.view", "print.any"
        ])
        self._role_permissions.setdefault("cashier", [
            "orders.create", "orders.view", "print.receipt"
        ])
        self._role_permissions.setdefault("kitchen", [
            "orders.view", "print.kitchen"
        ])
        self._role_permissions.setdefault("user", [])

    # ---------- User & Auth ----------
    def register(self, username: str, password: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
        username = username.strip().lower()
        if not username or not password:
            raise ValueError("username and password required")
        if username in self._users:
            raise ValueError("user already exists")
        roles = roles or ["user"]
        pwd = _hash_password(password)
        rec = {
            "username": username,
            "password": pwd,
            "roles": list(roles),
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }
        self._users[username] = rec
        return {k: v for k, v in rec.items() if k != "password"}

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        username = username.strip().lower()
        user = self._users.get(username)
        if not user or not _verify_password(user["password"], password):
            raise ValueError("invalid credentials")
        token = str(uuid.uuid4())
        self._tokens[token] = {"username": username, "issued_at": int(time.time())}
        return {"token": token, "user": {k: v for k, v in user.items() if k != "password"}}

    def logout(self, token: str) -> bool:
        if token in self._tokens:
            self._tokens.pop(token, None)
            return True
        return False

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        info = self._tokens.get(token)
        if not info:
            return None
        username = info["username"]
        user = self._users.get(username)
        if not user:
            return None
        return {k: v for k, v in user.items() if k != "password"}

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        username = username.strip().lower()
        user = self._users.get(username)
        if not user or not _verify_password(user["password"], old_password):
            raise ValueError("invalid credentials")
        user["password"] = _hash_password(new_password)
        user["updated_at"] = int(time.time())
        return True

    def has_role(self, token: str, role: str) -> bool:
        u = self.get_user_by_token(token)
        if not u:
            return False
        return role in u.get("roles", [])

    def list_users(self) -> List[Dict[str, Any]]:
        return [{k: v for k, v in u.items() if k != "password"} for u in self._users.values()]

    def delete_user(self, username: str) -> bool:
        username = username.strip().lower()
        if username in self._users:
            self._users.pop(username, None)
            # invalidate tokens for this user
            tokens_to_remove = [t for t, info in self._tokens.items() if info.get("username") == username]
            for t in tokens_to_remove:
                self._tokens.pop(t, None)
            return True
        return False

    # ---------- Role / Permission management ----------
    def set_role_permissions(self, role: str, permissions: List[str]) -> None:
        """
        تعیین یا بازنویسی مجوزهای یک نقش.
        """
        role = role.strip().lower()
        self._role_permissions[role] = list(permissions or [])

    def get_role_permissions(self, role: str) -> List[str]:
        return list(self._role_permissions.get(role.strip().lower(), []))

    def list_roles(self) -> List[str]:
        return list(self._role_permissions.keys())

    def get_permissions_for_user(self, token: str) -> List[str]:
        """
        بازگرداندن مجموعه مجوزهای کاربر بر اساس نقش‌هایش (ترکیب همه نقش‌ها).
        """
        u = self.get_user_by_token(token)
        if not u:
            return []
        perms = set()
        for r in u.get("roles", []):
            for p in self._role_permissions.get(r, []):
                perms.add(p)
        return sorted(perms)

    def has_permission(self, token: str, permission: str) -> bool:
        """
        بررسی اینکه آیا کاربر مرتبط با token دارای permission مشخص است.
        پشتیبانی از:
        - '*' به معنی همهٔ مجوزها
        - مجوز دقیق
        - namespace wildcard مثل 'orders.*'
        """
        if not token or not permission:
            return False
        perms = self.get_permissions_for_user(token)
        # اگر '*' در مجوزها باشد یعنی همهٔ مجوزها مجاز است
        if "*" in perms:
            return True
        if permission in perms:
            return True
        # بررسی namespace wildcard: 'orders.*'
        if "." in permission:
            ns = permission.split(".", 1)[0] + ".*"
            if ns in perms:
                return True
        # بررسی اینکه آیا هر مجوزی با الگوی 'xxx.*' وجود دارد که با permission تطابق داشته باشد
        for p in perms:
            if isinstance(p, str) and p.endswith(".*"):
                base = p[:-2]
                if permission.startswith(base + "."):
                    return True
        return False
