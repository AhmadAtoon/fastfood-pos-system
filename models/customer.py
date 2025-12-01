from datetime import datetime
from typing import Optional

class Customer:
    def __init__(
        self,
        customer_id: int,
        name: str,
        phone: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
        membership_code: Optional[str] = None,
        loyalty_points: int = 0,
        active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self.customer_id = customer_id
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.membership_code = membership_code
        self.loyalty_points = loyalty_points
        self.active = active
        self.created_at = created_at or datetime.now()

    # --- مدیریت اطلاعات پایه ---
    def update_name(self, new_name: str) -> None:
        if not new_name:
            raise ValueError("Name cannot be empty")
        self.name = new_name.strip()

    def update_contact(self, phone: Optional[str] = None, email: Optional[str] = None) -> None:
        if phone:
            self.phone = phone.strip()
        if email:
            self.email = email.strip()

    def update_address(self, new_address: str) -> None:
        if not new_address:
            raise ValueError("Address cannot be empty")
        self.address = new_address.strip()

    # --- کد اشتراک ---
    def assign_membership_code(self, code: str) -> None:
        if not code:
            raise ValueError("Membership code cannot be empty")
        self.membership_code = code.strip()

    def has_membership(self) -> bool:
        return self.membership_code is not None

    # --- سیستم وفاداری ---
    def add_loyalty_points(self, points: int) -> None:
        if points < 0:
            raise ValueError("Points must be positive")
        self.loyalty_points += points

    def redeem_loyalty_points(self, points: int) -> None:
        if points < 0:
            raise ValueError("Points must be positive")
        if points > self.loyalty_points:
            raise ValueError("Not enough loyalty points")
        self.loyalty_points -= points

    def get_loyalty_status(self) -> str:
        if self.loyalty_points >= 1000:
            return "Platinum"
        elif self.loyalty_points >= 500:
            return "Gold"
        elif self.loyalty_points >= 100:
            return "Silver"
        else:
            return "Bronze"

    # --- وضعیت فعال ---
    def deactivate(self) -> None:
        self.active = False

    def activate(self) -> None:
        self.active = True

    def __repr__(self) -> str:
        return f"<Customer id={self.customer_id} name={self.name} membership={self.membership_code or '-'} points={self.loyalty_points} status={self.get_loyalty_status()} active={self.active}>"
