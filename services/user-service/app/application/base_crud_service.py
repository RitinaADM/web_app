from typing import Generic, TypeVar, Optional
from domain.ports.outbound.base_repository import AbstractRepository

T = TypeVar("T")
ID = TypeVar("ID")

class BaseCrudService(Generic[T, ID]):
    def __init__(self, repo: AbstractRepository[T, ID]):
        self.repo = repo

    async def get_by_id(self, id: ID, request_id: str) -> Optional[T]:
        return await self.repo.get_by_id(id, request_id)

    async def create(self, entity: T, request_id: str) -> T:
        return await self.repo.create(entity, request_id)

    async def update(self, entity: T, request_id: str) -> T:
        return await self.repo.update(entity, request_id)

    async def delete(self, id: ID, request_id: str) -> None:
        await self.repo.delete(id, request_id)