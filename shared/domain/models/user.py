from datetime import datetime
from uuid import UUID

class User:
    def __init__(self, id: UUID, name: str, created_at: datetime, role: str = "user"):
        self._id = id
        self._name = name
        self._created_at = created_at
        self._role = role

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

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

    def set_role(self, role: str) -> None:
        if role not in ["user", "admin"]:
            raise ValueError("Role must be either 'user' or 'admin'")
        self._role = role