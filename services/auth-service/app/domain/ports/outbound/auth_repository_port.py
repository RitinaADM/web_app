from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from domain.models.auth_user import AuthUser

class AuthRepositoryPort(ABC):
    @abstractmethod
    async def create(self, auth_user: AuthUser, request_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID, request_id: str) -> Optional[AuthUser]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str, request_id: str) -> Optional[AuthUser]:
        pass

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: str, request_id: str) -> Optional[AuthUser]:
        pass

    @abstractmethod
    async def update(self, auth_user: AuthUser, request_id: str) -> None:
        pass