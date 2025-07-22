from datetime import datetime
from uuid import UUID
from typing import Optional, List

class AuthUser:
    def __init__(self, user_id: UUID, email: Optional[str], hashed_password: Optional[str], login_methods: List[str], created_at: datetime, telegram_id: Optional[str] = None):
        self._user_id = user_id
        self._email = email
        self._hashed_password = hashed_password
        self._login_methods = login_methods
        self._telegram_id = telegram_id
        self._created_at = created_at

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def hashed_password(self) -> Optional[str]:
        return self._hashed_password

    @property
    def login_methods(self) -> List[str]:
        return self._login_methods

    @property
    def telegram_id(self) -> Optional[str]:
        return self._telegram_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def set_hashed_password(self, hashed_password: str) -> None:
        if not hashed_password:
            raise ValueError("Hashed password cannot be empty")
        self._hashed_password = hashed_password

    def add_login_method(self, method: str) -> None:
        if method not in ["email", "google", "telegram"]:
            raise ValueError("Invalid login method")
        if method not in self._login_methods:
            self._login_methods.append(method)