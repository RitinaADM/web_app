from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from typing import Optional
from uuid import UUID
from datetime import datetime
from bson.binary import Binary, UUID_SUBTYPE
from domain.models.user import User
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
        """Преобразует объект User в словарь для MongoDB. Поле id (UUID) сохраняется как Binary UUID."""
        return {
            "_id": Binary(user.id.bytes, UUID_SUBTYPE),  # Сохраняем UUID как Binary
            "email": user.email,
            "name": user.name,
            "hashed_password": user.hashed_password,
            "created_at": user.created_at,
            "role": user.role
        }

    def _user_to_cache_dto(self, user: User) -> UserResponseDTO:
        """Преобразует объект User в DTO для кэширования."""
        return UserResponseDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            role=user.role
        )

    def _dict_to_user(self, data: dict) -> User:
        """Преобразует словарь (из MongoDB или кэша) в объект User."""
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Обрабатываем _id в зависимости от типа
        _id = data["_id"]
        if isinstance(_id, UUID):
            user_id = _id  # Уже UUID из кэша
        elif isinstance(_id, Binary):
            user_id = UUID(bytes=_id)  # Binary UUID из MongoDB
        else:
            user_id = UUID(_id)  # Строка UUID (для обратной совместимости)

        return User(
            id=user_id,
            email=data["email"],
            name=data["name"],
            hashed_password=data["hashed_password"],
            created_at=created_at,
            role=data.get("role", "user")
        )

    @log_execution_time
    async def create(self, user: User, request_id: str) -> User:
        logger = self.logger.bind(request_id=request_id)
        try:
            user_dict = self._user_to_dict(user)
            logger.info("Создание пользователя в MongoDB", user_id=str(user.id))
            await self.collection.insert_one(user_dict)
            logger.info("Пользователь создан в MongoDB", user_id=str(user.id))
            # Кэшируем пользователя с помощью DTO
            cache_dto = self._user_to_cache_dto(user)
            cache_data = cache_dto.model_dump(mode="json")  # Используем mode="json" для сериализации
            cache_data["hashed_password"] = user.hashed_password
            await self.cache.set(f"user:id:{user.id}", cache_data, settings.redis_ttl)
            await self.cache.set(f"user:email:{user.email}", cache_data, settings.redis_ttl)
            logger.info("Пользователь закэширован", user_id=str(user.id))
            return user
        except DuplicateKeyError as e:
            logger.error("Дублирующийся email в MongoDB", error=str(e), email=user.email)
            raise InvalidInputError(f"Email {user.email} уже существует")
        except Exception as e:
            logger.error("Не удалось создать пользователя в MongoDB", error=str(e), user_id=str(user.id))
            raise

    @log_execution_time
    async def get_by_id(self, user_id: UUID, request_id: str) -> Optional[User]:
        logger = self.logger.bind(request_id=request_id)
        try:
            # Проверяем кэш
            cache_key = f"user:id:{user_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info("Пользователь получен из кэша", user_id=str(user_id))
                # Десериализуем кэш в DTO
                cache_dto = UserResponseDTO.parse_obj(cached)
                return self._dict_to_user({
                    "_id": cache_dto.id,  # id из DTO уже UUID
                    "email": cache_dto.email,
                    "name": cache_dto.name,
                    "created_at": cache_dto.created_at,
                    "hashed_password": cached["hashed_password"],
                    "role": cache_dto.role
                })

            logger.info("Получение пользователя по ID из MongoDB", user_id=str(user_id))
            data = await self.collection.find_one({"_id": Binary(user_id.bytes, UUID_SUBTYPE)})
            if data:
                user = self._dict_to_user(data)
                # Кэшируем результат с помощью DTO
                cache_dto = self._user_to_cache_dto(user)
                cache_data = cache_dto.model_dump(mode="json")
                cache_data["hashed_password"] = user.hashed_password
                await self.cache.set(cache_key, cache_data, settings.redis_ttl)
                logger.info("Пользователь получен и закэширован", user_id=str(user_id))
                return user
            logger.warning("Пользователь не найден в MongoDB", user_id=str(user_id))
            return None
        except Exception as e:
            logger.error("Не удалось получить пользователя по ID", error=str(e), user_id=str(user_id))
            raise

    @log_execution_time
    async def get_by_email(self, email: str, request_id: str) -> Optional[User]:
        logger = self.logger.bind(request_id=request_id)
        try:
            # Проверяем кэш
            cache_key = f"user:email:{email}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info("Пользователь получен из кэша", email=email)
                # Десериализуем кэш в DTO
                cache_dto = UserResponseDTO.parse_obj(cached)
                return self._dict_to_user({
                    "_id": cache_dto.id,  # id из DTO уже UUID
                    "email": cache_dto.email,
                    "name": cache_dto.name,
                    "created_at": cache_dto.created_at,
                    "hashed_password": cached["hashed_password"],
                    "role": cache_dto.role
                })

            logger.info("Получение пользователя по email из MongoDB", email=email)
            data = await self.collection.find_one({"email": email})
            if data:
                user = self._dict_to_user(data)
                # Кэшируем результат с помощью DTO
                cache_dto = self._user_to_cache_dto(user)
                cache_data = cache_dto.model_dump(mode="json")
                cache_data["hashed_password"] = user.hashed_password
                await self.cache.set(cache_key, cache_data, settings.redis_ttl)
                logger.info("Пользователь получен и закэширован", email=email)
                return user
            logger.warning("Пользователь не найден по email в MongoDB", email=email)
            return None
        except Exception as e:
            logger.error("Не удалось получить пользователя по email", error=str(e), email=email)
            raise

    @log_execution_time
    async def update(self, user: User, request_id: str) -> User:
        logger = self.logger.bind(request_id=request_id)
        try:
            user_dict = self._user_to_dict(user)
            logger.info("Обновление пользователя в MongoDB", user_id=str(user.id))
            await self.collection.replace_one({"_id": Binary(user.id.bytes, UUID_SUBTYPE)}, user_dict)
            logger.info("Пользователь обновлен в MongoDB", user_id=str(user.id))
            # Инвалидируем кэш
            await self.cache.delete(f"user:id:{user.id}")
            await self.cache.delete(f"user:email:{user.email}")
            # Кэшируем обновленные данные с помощью DTO
            cache_dto = self._user_to_cache_dto(user)
            cache_data = cache_dto.model_dump(mode="json")
            cache_data["hashed_password"] = user.hashed_password
            await self.cache.set(f"user:id:{user.id}", cache_data, settings.redis_ttl)
            await self.cache.set(f"user:email:{user.email}", cache_data, settings.redis_ttl)
            logger.info("Пользователь закэширован", user_id=str(user.id))
            return user
        except DuplicateKeyError as e:
            logger.error("Дублирующийся email в MongoDB", error=str(e), email=user.email)
            raise InvalidInputError(f"Email {user.email} уже существует")
        except Exception as e:
            logger.error("Не удалось обновить пользователя в MongoDB", error=str(e), user_id=str(user.id))
            raise

    @log_execution_time
    async def delete(self, user_id: UUID, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Удаление пользователя из MongoDB", user_id=str(user_id))
            user = await self.get_by_id(user_id, request_id)
            await self.collection.delete_one({"_id": Binary(user_id.bytes, UUID_SUBTYPE)})
            logger.info("Пользователь удален из MongoDB", user_id=str(user_id))
            # Инвалидируем кэш
            if user:
                await self.cache.delete(f"user:id:{user_id}")
                await self.cache.delete(f"user:email:{user.email}")
        except Exception as e:
            logger.error("Не удалось удалить пользователя из MongoDB", error=str(e), user_id=str(user_id))
            raise