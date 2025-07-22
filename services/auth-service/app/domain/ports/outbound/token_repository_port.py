from abc import ABC, abstractmethod
from typing import Optional
from domain.models.token import RefreshToken, ResetToken

class TokenRepositoryPort(ABC):
    @abstractmethod
    async def store_refresh_token(self, token: RefreshToken, request_id: str) -> None:
        pass

    @abstractmethod
    async def get_refresh_token(self, token: str, request_id: str) -> Optional[RefreshToken]:
        pass

    @abstractmethod
    async def delete_refresh_token(self, token: str, request_id: str) -> None:
        pass

    @abstractmethod
    async def store_reset_token(self, token: ResetToken, request_id: str) -> None:
        pass

    @abstractmethod
    async def get_reset_token(self, token: str, request_id: str) -> Optional[ResetToken]:
        pass

    @abstractmethod
    async def delete_reset_token(self, token: str, request_id: str) -> None:
        pass