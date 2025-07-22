from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from typing import Optional
from uuid import UUID
from datetime import datetime
from bson.binary import Binary, UUID_SUBTYPE
from shared.domain.models.user import User  # Изменяем импорт
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from domain.ports.outbound.cache_port import CachePort
from domain.exceptions import InvalidInputError
from application.utils.logging_utils import log_execution_time
from application.dto.user_dto import UserResponseDTO
from structlog import get_logger
from config import settings

logger = get_logger(__name__)

class MongoUserRepository(UserRepositoryPort):
    def __init__(self, collection: Collection, cache: CachePort):
        self.collection = collection
        self.cache = cache
        self.logger = logger.bind(repository="MongoUserRepository")

    def _user_to_dict(self, user: User) -> dict:
        return {
            "_id": Binary(user.id.bytes, UUID_SUBTYPE),
            "name": user.name,
            "created_at": user.created_at,
            "role": user.role
        }

    def _user_to_cache_dto(self, user: User) -> UserResponseDTO:
        return UserResponseDTO(
            id=user.id,
            name=user.name,
            created_at=user.created_at,
            role=user.role
        )

    def _dict_to_user(self, data: dict) -> User:
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        _id = data["_id"]
        if isinstance(_id, UUID):
            user_id = _id
        elif isinstance(_id, Binary):
            user_id = UUID(bytes=_id)
        else:
            user_id = UUID(_id)

        return User(
            id=user_id,
            name=data["name"],
            created_at=created_at,
            role=data.get("role", "user")
        )

    @log_execution_time
    async def create(self, user: User, request_id: str) -> User:
        logger = self.logger.bind(request_id=request_id)
        try:
            user_dict = self._user_to_dict(user)
            logger.info("Creating user in MongoDB", user_id=str(user.id))
            await self.collection.insert_one(user_dict)
            logger.info("User created in MongoDB", user_id=str(user.id))
            cache_dto = self._user_to_cache_dto(user)
            cache_data = cache_dto.model_dump(mode="json")
            await self.cache.set(f"user:id:{user.id}", cache_data, settings.redis_ttl)
            logger.info("User cached", user_id=str(user.id))
            return user
        except DuplicateKeyError as e:
            logger.error("Duplicate key in MongoDB", error=str(e))
            raise InvalidInputError("User already exists")
        except Exception as e:
            logger.error("Failed to create user in MongoDB", error=str(e), user_id=str(user.id))
            raise

    @log_execution_time
    async def get_by_id(self, user_id: UUID, request_id: str) -> Optional[User]:
        logger = self.logger.bind(request_id=request_id)
        try:
            cache_key = f"user:id:{user_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info("User retrieved from cache", user_id=str(user_id))
                cache_dto = UserResponseDTO.parse_obj(cached)
                return self._dict_to_user({
                    "_id": cache_dto.id,
                    "name": cache_dto.name,
                    "created_at": cache_dto.created_at,
                    "role": cache_dto.role
                })

            logger.info("Fetching user by ID from MongoDB", user_id=str(user_id))
            data = await self.collection.find_one({"_id": Binary(user_id.bytes, UUID_SUBTYPE)})
            if data:
                user = self._dict_to_user(data)
                cache_dto = self._user_to_cache_dto(user)
                cache_data = cache_dto.model_dump(mode="json")
                await self.cache.set(cache_key, cache_data, settings.redis_ttl)
                logger.info("User retrieved and cached", user_id=str(user_id))
                return user
            logger.warning("User not found in MongoDB", user_id=str(user_id))
            return None
        except Exception as e:
            logger.error("Failed to fetch user by ID", error=str(e), user_id=str(user_id))
            raise

    @log_execution_time
    async def update(self, user: User, request_id: str) -> User:
        logger = self.logger.bind(request_id=request_id)
        try:
            user_dict = self._user_to_dict(user)
            logger.info("Updating user in MongoDB", user_id=str(user.id))
            await self.collection.replace_one({"_id": Binary(user.id.bytes, UUID_SUBTYPE)}, user_dict)
            logger.info("User updated in MongoDB", user_id=str(user.id))
            await self.cache.delete(f"user:id:{user.id}")
            cache_dto = self._user_to_cache_dto(user)
            cache_data = cache_dto.model_dump(mode="json")
            await self.cache.set(f"user:id:{user.id}", cache_data, settings.redis_ttl)
            logger.info("User cached", user_id=str(user.id))
            return user
        except Exception as e:
            logger.error("Failed to update user in MongoDB", error=str(e), user_id=str(user.id))
            raise

    @log_execution_time
    async def delete(self, user_id: UUID, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Deleting user from MongoDB", user_id=str(user_id))
            await self.collection.delete_one({"_id": Binary(user_id.bytes, UUID_SUBTYPE)})
            logger.info("User deleted from MongoDB", user_id=str(user_id))
            await self.cache.delete(f"user:id:{user_id}")
        except Exception as e:
            logger.error("Failed to delete user from MongoDB", error=str(e), user_id=str(user_id))
            raise

    @log_execution_time
    async def get_by_email(self, email: str, request_id: str) -> Optional[User]:
        logger = self.logger.bind(request_id=request_id)
        logger.error("get_by_email is not supported in user-service, use auth-service instead")
        raise NotImplementedError("Email-based queries are handled by auth-service")