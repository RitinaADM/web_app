import grpc
import jwt
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from config import settings
from domain.ports.outbound.user_service_client_port import UserServiceClientPort
from shared.domain.models.user import User  # Изменяем импорт
from domain.exceptions import InvalidInputError
from application.utils.logging_utils import log_execution_time
from . import user_pb2, user_pb2_grpc
from structlog import get_logger

logger = get_logger(__name__)

class UserServiceClient(UserServiceClientPort):
    def __init__(self):
        self.channel = grpc.aio.insecure_channel(settings.user_service_grpc_host)
        self.stub = user_pb2_grpc.AdminServiceStub(self.channel)
        self.logger = logger.bind(service="UserServiceClient")
        self.service_jwt = jwt.encode(
            {"role": "admin", "exp": datetime.utcnow() + timedelta(days=365)},
            settings.jwt_secret_key,
            algorithm="HS256"
        )

    @log_execution_time
    async def create_user(self, user_id: UUID, name: str, role: str, request_id: str) -> User:
        logger = self.logger.bind(request_id=request_id)
        try:
            metadata = [("authorization", f"Bearer {self.service_jwt}")]
            response = await self.stub.CreateUser(
                user_pb2.CreateUserRequest(id=str(user_id), name=name, role=role),
                metadata=metadata
            )
            user = User(
                id=UUID(response.id),
                name=response.name,
                created_at=datetime.fromisoformat(response.created_at.replace("Z", "+00:00")),
                role=response.role
            )
            logger.info("User created via user-service", user_id=str(user_id))
            return user
        except grpc.RpcError as e:
            logger.error("Failed to create user", error=str(e))
            if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise InvalidInputError(str(e))
            raise RuntimeError(f"Failed to create user: {str(e)}")

    @log_execution_time
    async def get_user_by_id(self, user_id: UUID, request_id: str) -> Optional[User]:
        logger = self.logger.bind(request_id=request_id)
        try:
            metadata = [("authorization", f"Bearer {self.service_jwt}")]
            response = await self.stub.GetUser(
                user_pb2.GetUserRequest(id=str(user_id)),
                metadata=metadata
            )
            user = User(
                id=UUID(response.id),
                name=response.name,
                created_at=datetime.fromisoformat(response.created_at.replace("Z", "+00:00")),
                role=response.role
            )
            logger.info("User fetched by ID", user_id=str(user_id))
            return user
        except grpc.RpcError as e:
            logger.error("Failed to get user by ID", error=str(e), user_id=str(user_id))
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise RuntimeError(f"Failed to get user: {str(e)}")