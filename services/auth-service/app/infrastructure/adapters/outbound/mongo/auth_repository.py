from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from typing import Optional
from uuid import UUID
from datetime import datetime
from bson.binary import Binary, UUID_SUBTYPE
from domain.models.auth_user import AuthUser
from domain.exceptions import InvalidInputError
from application.utils.logging_utils import log_execution_time
from structlog import get_logger

from domain.ports.outbound.auth_repository_port import AuthRepositoryPort

logger = get_logger(__name__)


class MongoAuthRepository(AuthRepositoryPort):
    def __init__(self, collection: Collection):
        self.collection = collection
        self.logger = logger.bind(repository="MongoAuthRepository")

    def _auth_user_to_dict(self, auth_user: AuthUser) -> dict:
        return {
            "_id": Binary(auth_user.user_id.bytes, UUID_SUBTYPE),
            "email": auth_user.email,
            "hashed_password": auth_user.hashed_password,
            "login_methods": auth_user.login_methods,
            "telegram_id": auth_user.telegram_id,
            "created_at": auth_user.created_at
        }

    def _dict_to_auth_user(self, data: dict) -> AuthUser:
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Handle different types of _id
        _id = data["_id"]
        if isinstance(_id, UUID):
            user_id = _id  # Already a UUID, no conversion needed
        elif isinstance(_id, Binary):
            user_id = UUID(bytes=_id)  # Convert Binary to UUID
        else:
            user_id = UUID(_id)  # Assume string and convert to UUID

        return AuthUser(
            user_id=user_id,
            email=data["email"],
            hashed_password=data["hashed_password"],
            login_methods=data["login_methods"],
            telegram_id=data.get("telegram_id"),
            created_at=created_at
        )

    @log_execution_time
    async def create(self, auth_user: AuthUser, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            user_dict = self._auth_user_to_dict(auth_user)
            logger.info("Creating auth user in MongoDB", user_id=str(auth_user.user_id))
            await self.collection.insert_one(user_dict)
            logger.info("Auth user created in MongoDB", user_id=str(auth_user.user_id))
        except DuplicateKeyError as e:
            logger.error("Duplicate email or telegram_id in MongoDB", error=str(e))
            raise InvalidInputError("Email or Telegram ID already exists")
        except Exception as e:
            logger.error("Failed to create auth user in MongoDB", error=str(e))
            raise

    @log_execution_time
    async def get_by_id(self, user_id: UUID, request_id: str) -> Optional[AuthUser]:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Fetching auth user by ID from MongoDB", user_id=str(user_id))
            data = await self.collection.find_one({"_id": Binary(user_id.bytes, UUID_SUBTYPE)})
            if data:
                logger.info("Auth user fetched", user_id=str(user_id))
                return self._dict_to_auth_user(data)
            logger.warning("Auth user not found in MongoDB", user_id=str(user_id))
            return None
        except Exception as e:
            logger.error("Failed to fetch auth user by ID", error=str(e), user_id=str(user_id))
            raise

    @log_execution_time
    async def get_by_email(self, email: str, request_id: str) -> Optional[AuthUser]:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Fetching auth user by email from MongoDB", email=email)
            data = await self.collection.find_one({"email": email})
            if data:
                logger.info("Auth user fetched", email=email)
                return self._dict_to_auth_user(data)
            logger.warning("Auth user not found in MongoDB", email=email)
            return None
        except Exception as e:
            logger.error("Failed to fetch auth user by email", error=str(e), email=email)
            raise

    @log_execution_time
    async def get_by_telegram_id(self, telegram_id: str, request_id: str) -> Optional[AuthUser]:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Fetching auth user by telegram_id from MongoDB", telegram_id=telegram_id)
            data = await self.collection.find_one({"telegram_id": telegram_id})
            if data:
                logger.info("Auth user fetched", telegram_id=telegram_id)
                return self._dict_to_auth_user(data)
            logger.warning("Auth user not found in MongoDB", telegram_id=telegram_id)
            return None
        except Exception as e:
            logger.error("Failed to fetch auth user by telegram_id", error=str(e), telegram_id=telegram_id)
            raise

    @log_execution_time
    async def update(self, auth_user: AuthUser, request_id: str) -> None:
        logger = self.logger.bind(request_id=request_id)
        try:
            user_dict = self._auth_user_to_dict(auth_user)
            logger.info("Updating auth user in MongoDB", user_id=str(auth_user.user_id))
            await self.collection.replace_one({"_id": Binary(auth_user.user_id.bytes, UUID_SUBTYPE)}, user_dict)
            logger.info("Auth user updated in MongoDB", user_id=str(auth_user.user_id))
        except DuplicateKeyError as e:
            logger.error("Duplicate email or telegram_id in MongoDB", error=str(e))
            raise InvalidInputError("Email or Telegram ID already exists")
        except Exception as e:
            logger.error("Failed to update auth user in MongoDB", error=str(e))
            raise