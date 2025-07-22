from abc import ABC, abstractmethod
from typing import Optional, Any

class CachePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша по ключу."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Установить значение в кэш с указанным TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Удалить значение из кэша по ключу."""
        pass