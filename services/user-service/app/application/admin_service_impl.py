from uuid import UUID
from datetime import datetime
from typing import Optional
from domain.ports.inbound.admin_usecase_port import AdminUseCasePort
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from shared.domain.models.user import User  # Изменяем импорт
from domain.exceptions import UserNotFoundError, InvalidInputError
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO, UserIdDTO, UserResponseDTO
from application.utils.logging_utils import log_execution_time
from structlog import get_logger

logger = get_logger(__name__)

class AdminService(AdminUseCasePort):
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo
        self.logger = logger.bind(service="AdminService")

    @log_execution_time
    async def create_user(self, user_dto: CreateUserDTO, request_id: str) -> UserResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Creating user", input_data=user_dto.dict())
            user = User(
                id=user_dto.id,
                name=user_dto.name,
                created_at=datetime.utcnow(),
                role=user_dto.role
            )
            created_user = await self.repo.create(user, request_id)
            response = UserResponseDTO(
                id=created_user.id,
                name=created_user.name,
                created_at=created_user.created_at,
                role=created_user.role
            )
            logger.info("User created successfully", user_id=str(user.id), response=response.dict())
            return response
        except InvalidInputError as e:
            logger.error("Invalid input for creating user", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in creating user", error=str(e))
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
                name=user.name,
                created_at=user.created_at,
                role=user.role
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
            updated_user = await self.repo.update(user, request_id)
            response = UserResponseDTO(
                id=updated_user.id,
                name=updated_user.name,
                created_at=updated_user.created_at,
                role=updated_user.role
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