import json
from typing import Optional, Any
from redis.asyncio import Redis
from domain.ports.outbound.cache_port import CachePort
from structlog import get_logger
from application.utils.logging_utils import log_execution_time

logger = get_logger(__name__)

class RedisCacheRepository(CachePort):
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.logger = logger.bind(repository="RedisCacheRepository")

    @log_execution_time
    async def get(self, key: str) -> Optional[Any]:
        logger = self.logger.bind(key=key)
        try:
            value = await self.redis.get(key)
            if value:
                logger.info("Кэш найден", key=key)
                return json.loads(value)
            logger.info("Кэш не найден", key=key)
            return None
        except Exception as e:
            logger.error("Ошибка при получении из кэша", error=str(e), key=key)
            raise

    @log_execution_time
    async def set(self, key: str, value: Any, ttl: int) -> None:
        logger = self.logger.bind(key=key)
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
            logger.info("Значение установлено в кэш", key=key, ttl=ttl)
        except Exception as e:
            logger.error("Ошибка при установке в кэш", error=str(e), key=key)
            raise

    @log_execution_time
    async def delete(self, key: str) -> None:
        logger = self.logger.bind(key=key)
        try:
            await self.redis.delete(key)
            logger.info("Значение удалено из кэша", key=key)
        except Exception as e:
            logger.error("Ошибка при удалении из кэша", error=str(e), key=key)
            raise