from abc import abstractmethod
from typing import Optional
from uuid import UUID
from domain.models.user import User
from domain.ports.outbound.base_repository import AbstractRepository

class UserRepositoryPort(AbstractRepository[User, UUID]):
    @abstractmethod
    async def get_by_email(self, email: str, request_id: str) -> Optional[User]: ...