from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from application.dto.user_dto import UserIdDTO, UpdateNameDTO, UserResponseDTO

class UserServicePort(ABC):
    @abstractmethod
    async def get_my_profile(self, user_id_dto: UserIdDTO, request_id: str) -> Optional[UserResponseDTO]: ...

    @abstractmethod
    async def update_my_name(self, user_id: UUID, name_dto: UpdateNameDTO, request_id: str) -> Optional[UserResponseDTO]: ...