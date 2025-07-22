from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from shared.domain.models.user import User  # Изменяем импорт

class UserServiceClientPort(ABC):
    @abstractmethod
    async def create_user(self, user_id: UUID, name: str, role: str, request_id: str) -> User:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID, request_id: str) -> Optional[User]:
        pass