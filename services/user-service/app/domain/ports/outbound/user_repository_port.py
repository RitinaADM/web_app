from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from shared.domain.models.user import User  # Изменяем импорт
from domain.ports.outbound.base_repository import AbstractRepository

class UserRepositoryPort(AbstractRepository[User, UUID]):
    @abstractmethod
    async def get_by_email(self, email: str, request_id: str) -> Optional[User]:
        """
        Метод заглушка, так как email теперь обрабатывается в auth-service.
        """
        raise NotImplementedError("Email-based queries are handled by auth-service")