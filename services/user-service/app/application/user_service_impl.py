from uuid import UUID
from typing import Optional
from domain.ports.inbound.user_service_port import UserServicePort
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from shared.domain.models.user import User  # Изменяем импорт
from domain.exceptions import UserNotFoundError, InvalidInputError
from application.dto.user_dto import UserIdDTO, UpdateNameDTO, UserResponseDTO
from application.utils.logging_utils import log_execution_time
from structlog import get_logger

logger = get_logger(__name__)

class UserService(UserServicePort):
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo
        self.logger = logger.bind(service="UserService")

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
                name=user.name,
                created_at=user.created_at,
                role=user.role
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
                name=updated_user.name,
                created_at=updated_user.created_at,
                role=updated_user.role
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