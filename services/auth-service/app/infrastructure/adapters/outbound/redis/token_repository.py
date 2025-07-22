import json
from typing import Optional
from redis.asyncio import Redis
from uuid import UUID
from domain.ports.outbound.token_repository_port import TokenRepositoryPort
from domain.models.token import RefreshToken, ResetToken
from structlog import get_logger
from application.utils.logging_utils import log_execution_time
from config import settings

logger = get_logger(__name__)

class RedisTokenRepository(TokenRepositoryPort):
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.logger = logger.bind(repository="RedisTokenRepository")

    @log_execution_time
    async def store_refresh_token(self, token: RefreshToken, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            key = f"refresh_token:{token.token}"
            data = {"user_id": str(token.user_id)}
            await self.redis.setex(key, settings.redis_ttl, json.dumps(data))
            logger.info("Refresh token stored", key=key)
        except Exception as e:
            logger.error("Failed to store refresh token", error=str(e), key=key)
            raise

    @log_execution_time
    async def get_refresh_token(self, token: str, request_id: str) -> Optional[RefreshToken]:
        logger = self.logger.bind(request_id=request_id)
        try:
            key = f"refresh_token:{token}"
            data = await self.redis.get(key)
            if data:
                data_dict = json.loads(data)
                return RefreshToken(token=token, user_id=UUID(data_dict["user_id"]))
            logger.info("Refresh token not found", key=key)
            return None
        except Exception as e:
            logger.error("Failed to get refresh token", error=str(e), key=key)
            raise

    @log_execution_time
    async def delete_refresh_token(self, token: str, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            key = f"refresh_token:{token}"
            await self.redis.delete(key)
            logger.info("Refresh token deleted", key=key)
        except Exception as e:
            logger.error("Failed to delete refresh token", error=str(e), key=key)
            raise

    @log_execution_time
    async def store_reset_token(self, token: ResetToken, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            key = f"reset_token:{token.token}"
            data = {"user_id": str(token.user_id)}
            await self.redis.setex(key, token.ttl, json.dumps(data))
            logger.info("Reset token stored", key=key, ttl=token.ttl)
        except Exception as e:
            logger.error("Failed to store reset token", error=str(e), key=key)
            raise

    @log_execution_time
    async def get_reset_token(self, token: str, request_id: str) -> Optional[ResetToken]:
        logger = self.logger.bind(request_id=request_id)
        try:
            key = f"reset_token:{token}"
            data = await self.redis.get(key)
            if data:
                data_dict = json.loads(data)
                return ResetToken(token=token, user_id=UUID(data_dict["user_id"]), ttl=3600)
            logger.info("Reset token not found", key=key)
            return None
        except Exception as e:
            logger.error("Failed to get reset token", error=str(e), key=key)
            raise

    @log_execution_time
    async def delete_reset_token(self, token: str, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            key = f"reset_token:{token}"
            await self.redis.delete(key)
            logger.info("Reset token deleted", key=key)
        except Exception as e:
            logger.error("Failed to delete reset token", error=str(e), key=key)
            raise