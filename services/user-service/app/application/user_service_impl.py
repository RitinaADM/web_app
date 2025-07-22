import bcrypt
import jwt
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional
from domain.ports.inbound.user_service_port import UserServicePort
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from domain.models.user import User
from domain.exceptions import AuthenticationError, UserNotFoundError, InvalidInputError
from application.dto.user_dto import LoginDTO, UserIdDTO, UpdateNameDTO, UserResponseDTO
from application.utils.logging_utils import log_execution_time, filter_sensitive_data
from structlog import get_logger

logger = get_logger(__name__)

class UserService(UserServicePort):
    def __init__(self, repo: UserRepositoryPort, jwt_secret_key: str):
        self.repo = repo
        self.secret_key = jwt_secret_key
        self.logger = logger.bind(service="UserService")

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    @log_execution_time
    async def login(self, login_dto: LoginDTO, request_id: str) -> str:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Processing login", email=login_dto.email)
            user = await self.repo.get_by_email(login_dto.email, request_id)
            if not user or not self._verify_password(login_dto.password, user.hashed_password):
                logger.error("Invalid credentials", email=login_dto.email)
                raise AuthenticationError("Invalid email or password")
            payload = {
                "user_id": str(user.id),
                "role": user.role,  # Добавляем роль в токен
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            logger.info("User logged in successfully", user_id=str(user.id), role=user.role)
            return token
        except AuthenticationError as e:
            logger.error("Authentication failed", error=str(e), email=login_dto.email)
            raise
        except InvalidInputError as e:
            logger.error("Invalid input for login", error=str(e), email=login_dto.email)
            raise
        except Exception as e:
            logger.error("Unexpected error in login", error=str(e), email=login_dto.email)
            raise AuthenticationError(f"Unexpected error in login: {str(e)}")

    @log_execution_time
    async def get_my_profile(self, user_id_dto: UserIdDTO, request_id: str) -> Optional[UserResponseDTO]:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Fetching user profile", user_id=str(user_id_dto.id))
            user = await self.repo.get_by_id(user_id_dto.id, request_id)
            if not user:
                logger.warning("User not found", user_id=str(user_id_dto.id))
                raise UserNotFoundError(f"User with ID {user_id_dto.id} not found")
            response = UserResponseDTO(
                id=user.id,
                email=user.email,
                name=user.name,
                created_at=user.created_at
            )
            logger.info("User profile fetched successfully", response=response.dict())
            return response
        except UserNotFoundError as e:
            logger.error("User not found", error=str(e), user_id=str(user_id_dto.id))
            raise
        except InvalidInputError as e:
            logger.error("Invalid input for getting profile", error=str(e), user_id=str(user_id_dto.id))
            raise
        except Exception as e:
            logger.error("Unexpected error in getting profile", error=str(e), user_id=str(user_id_dto.id))
            raise RuntimeError(f"Unexpected error in getting profile: {str(e)}")

    @log_execution_time
    async def update_my_name(self, user_id: UUID, name_dto: UpdateNameDTO, request_id: str) -> Optional[UserResponseDTO]:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Updating user name", user_id=str(user_id), new_name=name_dto.name)
            user = await self.repo.get_by_id(user_id, request_id)
            if not user:
                logger.warning("User not found", user_id=str(user_id))
                raise UserNotFoundError(f"User with ID {user_id} not found")
            user.set_name(name_dto.name)
            updated_user = await self.repo.update(user, request_id)
            response = UserResponseDTO(
                id=updated_user.id,
                email=updated_user.email,
                name=updated_user.name,
                created_at=updated_user.created_at
            )
            logger.info("User name updated successfully", response=response.dict())
            return response
        except UserNotFoundError as e:
            logger.error("User not found", error=str(e), user_id=str(user_id))
            raise
        except InvalidInputError as e:
            logger.error("Invalid input for updating name", error=str(e), user_id=str(user_id))
            raise
        except Exception as e:
            logger.error("Unexpected error in updating name", error=str(e), user_id=str(user_id))
            raise RuntimeError(f"Unexpected error in updating name: {str(e)}")