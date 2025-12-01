# services/auth_decorators.py
import inspect
from functools import wraps
from typing import Optional, Callable, Any
from services.auth_service import AuthService

def requires_permission(auth_service: Optional[AuthService], permission: str):
    """
    دکوراتور برای چک مجوز.
    - اگر auth_service None باشد، چک نادیده گرفته می‌شود.
    - دکوراتور تلاش می‌کند actor_token را از kwargs یا positional args استخراج کند.
    - اگر actor_token پیدا نشود و auth_service موجود باشد، PermissionError پرتاب می‌شود.
    """
    def decorator(func: Callable[..., Any]):
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not auth_service:
                return func(*args, **kwargs)

            # تلاش برای استخراج actor_token از kwargs
            token = kwargs.get("actor_token", None)

            # اگر در kwargs نبود، سعی می‌کنیم از positional args با توجه به نام پارامترها استخراج کنیم
            if token is None:
                bound = None
                try:
                    bound = sig.bind_partial(*args, **kwargs)
                except Exception:
                    bound = None
                if bound:
                    # اگر پارامتر actor_token در امضای تابع وجود دارد، آن را از bound.arguments بگیریم
                    if "actor_token" in bound.arguments:
                        token = bound.arguments.get("actor_token", None)
                    else:
                        # اگر نام متفاوتی استفاده شده باشد، تلاش برای یافتن هر پارامتری که نامش token-like است
                        for name, val in bound.arguments.items():
                            if name.lower() in ("token", "actor_token", "auth_token", "user_token"):
                                token = val
                                break

            if token is None:
                raise PermissionError("Missing actor token for permission check")

            if not auth_service.has_permission(token, permission):
                raise PermissionError(f"Permission denied: {permission}")

            return func(*args, **kwargs)
        return wrapper
    return decorator
