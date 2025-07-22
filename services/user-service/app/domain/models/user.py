from datetime import datetime
from uuid import UUID

class User:
    def __init__(self, id: UUID, email: str, name: str, hashed_password: str, created_at: datetime, role: str = "user"):
        self._id = id
        self._email = email
        self._name = name
        self._hashed_password = hashed_password
        self._created_at = created_at
        self._role = role  # Добавляем поле role с дефолтным значением "user"

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def email(self) -> str:
        return self._email

    @property
    def name(self) -> str:
        return self._name

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def role(self) -> str:
        return self._role

    def set_name(self, name: str) -> None:
        if not name or len(name) > 100:
            raise ValueError("Name must be non-empty and less than 100 characters")
        self._name = name

    def set_email(self, email: str) -> None:
        if not isinstance(email, str) or "@" not in email:
            raise ValueError("Invalid email format")
        self._email = email

    def set_role(self, role: str) -> None:
        if role not in ["user", "admin"]:
            raise ValueError("Role must be either 'user' or 'admin'")
        self._role = role