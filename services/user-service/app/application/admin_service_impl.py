import bcrypt
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from domain.ports.inbound.admin_usecase_port import AdminUseCasePort
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from domain.models.user import User
from domain.exceptions import UserNotFoundError, InvalidInputError
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO, UserIdDTO, UserResponseDTO
from application.utils.logging_utils import log_execution_time, filter_sensitive_data
from structlog import get_logger

logger = get_logger(__name__)

class AdminService(AdminUseCasePort):
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo
        self.logger = logger.bind(service="AdminService")

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @log_execution_time
    async def create_user(self, user_dto: CreateUserDTO, request_id: str) -> UserResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            # Проверяем, существует ли пользователь с таким email
            existing_user = await self.repo.get_by_email(user_dto.email, request_id)
            if existing_user:
                logger.error("Email already exists", email=user_dto.email)
                raise InvalidInputError(f"Email {user_dto.email} уже существует")

            # Назначаем роль: admin для определённых email, иначе user
            role = "admin" if user_dto.email == "admin@example.com" else "user"
            logger.info("Creating user", input_data=filter_sensitive_data(user_dto.dict()), role=role)
            user = User(
                id=uuid4(),
                email=user_dto.email,
                name=user_dto.name,
                hashed_password=self._hash_password(user_dto.password),
                created_at=datetime.utcnow(),
                role=role
            )
            created_user = await self.repo.create(user, request_id)
            response = UserResponseDTO(
                id=created_user.id,
                email=created_user.email,
                name=created_user.name,
                created_at=created_user.created_at
            )
            logger.info("User created successfully", user_id=str(user.id), response=response.dict())
            return response
        except InvalidInputError as e:
            logger.error("Invalid input for creating user", error=str(e), email=user_dto.email)
            raise
        except Exception as e:
            logger.error("Unexpected error in creating user", error=str(e), email=user_dto.email)
            raise RuntimeError(f"Unexpected error in creating user: {str(e)}")

    @log_execution_time
    async def get_user(self, user_id_dto: UserIdDTO, request_id: str) -> UserResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Fetching user", user_id=str(user_id_dto.id))
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
            logger.info("User fetched successfully", response=response.dict())
            return response
        except UserNotFoundError as e:
            logger.error("User not found", error=str(e), user_id=str(user_id_dto.id))
            raise
        except InvalidInputError as e:
            logger.error("Invalid input for getting user", error=str(e), user_id=str(user_id_dto.id))
            raise
        except Exception as e:
            logger.error("Unexpected error in getting user", error=str(e), user_id=str(user_id_dto.id))
            raise RuntimeError(f"Unexpected error in getting user: {str(e)}")

    @log_execution_time
    async def update_user(self, user_id: UUID, user_dto: UpdateUserDTO, request_id: str) -> UserResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Updating user", user_id=str(user_id), input_data=user_dto.dict())
            user = await self.repo.get_by_id(user_id, request_id)
            if not user:
                logger.warning("User not found", user_id=str(user_id))
                raise UserNotFoundError(f"User with ID {user_id} not found")
            user.set_name(user_dto.name)
            user.set_email(user_dto.email)
            updated_user = await self.repo.update(user, request_id)
            response = UserResponseDTO(
                id=updated_user.id,
                email=updated_user.email,
                name=updated_user.name,
                created_at=updated_user.created_at
            )
            logger.info("User updated successfully", response=response.dict())
            return response
        except UserNotFoundError as e:
            logger.error("User not found", error=str(e), user_id=str(user_id))
            raise
        except InvalidInputError as e:
            logger.error("Invalid input for updating user", error=str(e), user_id=str(user_id))
            raise
        except Exception as e:
            logger.error("Unexpected error in updating user", error=str(e), user_id=str(user_id))
            raise RuntimeError(f"Unexpected error in updating user: {str(e)}")

    @log_execution_time
    async def delete_user(self, user_id_dto: UserIdDTO, request_id: str) -> bool:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Deleting user", user_id=str(user_id_dto.id))
            user = await self.repo.get_by_id(user_id_dto.id, request_id)
            if not user:
                logger.warning("User not found", user_id=str(user_id_dto.id))
                raise UserNotFoundError(f"User with ID {user_id_dto.id} not found")
            await self.repo.delete(user_id_dto.id, request_id)
            logger.info("User deleted successfully", user_id=str(user_id_dto.id))
            return True
        except UserNotFoundError as e:
            logger.error("User not found", error=str(e), user_id=str(user_id_dto.id))
            raise
        except InvalidInputError as e:
            logger.error("Invalid input for deleting user", error=str(e), user_id=str(user_id_dto.id))
            raise
        except Exception as e:
            logger.error("Unexpected error in deleting user", error=str(e), user_id=str(user_id_dto.id))
            raise RuntimeError(f"Unexpected error in deleting user: {str(e)}")