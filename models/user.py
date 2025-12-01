# models/user.py
from datetime import datetime
from typing import Optional

class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        role: str,
        email: Optional[str] = None,
        active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.username = username
        self.password = password  # در نسخه واقعی باید هش شود
        self.role = role.lower().strip()
        self.email = email
        self.active = active
        self.created_at = created_at or datetime.now()

    def check_password(self, password: str) -> bool:
        return self.password == password

    def change_password(self, new_password: str) -> None:
        if not new_password or len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters")
        self.password = new_password

    def is_admin(self) -> bool:
        return self.role == "admin"

    def set_role(self, new_role: str) -> None:
        if not new_role:
            raise ValueError("Role cannot be empty")
        self.role = new_role.lower().strip()

    def deactivate(self) -> None:
        self.active = False

    def activate(self) -> None:
        self.active = True

    def __repr__(self) -> str:
        return f"<User id={self.user_id} username={self.username} role={self.role} active={self.active}>"
