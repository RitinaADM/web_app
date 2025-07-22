from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO, UserIdDTO, UserResponseDTO

class AdminUseCasePort(ABC):
    @abstractmethod
    async def create_user(self, user_dto: CreateUserDTO, request_id: str) -> UserResponseDTO: ...

    @abstractmethod
    async def get_user(self, user_id_dto: UserIdDTO, request_id: str) -> Optional[UserResponseDTO]: ...

    @abstractmethod
    async def update_user(self, user_id: UUID, user_dto: UpdateUserDTO, request_id: str) -> Optional[UserResponseDTO]: ...

    @abstractmethod
    async def delete_user(self, user_id_dto: UserIdDTO, request_id: str) -> bool: ...