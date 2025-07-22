from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar("T")
ID = TypeVar("ID")

class AbstractRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id: ID, request_id: str) -> Optional[T]: ...

    @abstractmethod
    async def create(self, entity: T, request_id: str) -> T: ...

    @abstractmethod
    async def update(self, entity: T, request_id: str) -> T: ...

    @abstractmethod
    async def delete(self, id: ID, request_id: str) -> None: ...