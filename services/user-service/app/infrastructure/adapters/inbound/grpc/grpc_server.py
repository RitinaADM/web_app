import grpc
import asyncio
import jwt
from grpc.aio import server as aio_server
from grpc_reflection.v1alpha import reflection
from uuid import UUID
from functools import wraps
from dishka import AsyncContainer
from config import settings
from infrastructure.di.container import get_container
from application.user_service_impl import UserService
from application.admin_service_impl import AdminService
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO, UserIdDTO, UpdateNameDTO
from application.utils.logging_utils import generate_request_id, log_execution_time
from application.utils.grpc_utils import handle_grpc_exceptions
from domain.exceptions import AuthenticationError, InvalidInputError
from . import user_pb2_grpc, user_pb2
from structlog import get_logger

logger = get_logger(__name__)

SERVICE_NAMES = (
    user_pb2.DESCRIPTOR.services_by_name['AdminService'].full_name,
    user_pb2.DESCRIPTOR.services_by_name['UserService'].full_name,
    reflection.SERVICE_NAME,
)

def jwt_auth_middleware(func):
    @wraps(func)
    async def wrapper(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        metadata = dict(context.invocation_metadata())
        token = metadata.get('authorization')
        if not token:
            logger.error("No authorization token provided")
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Authorization token required")
            raise AuthenticationError("Authorization token required")
        try:
            payload = jwt.decode(token.replace("Bearer ", ""), settings.jwt_secret_key, algorithms=["HS256"])
            user_id = UUID(payload['user_id'])
        except (jwt.InvalidTokenError, KeyError) as e:
            logger.error("Invalid JWT token", error=str(e))
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(f"Invalid JWT token: {str(e)}")
            raise AuthenticationError(f"Invalid JWT token: {str(e)}")
        return await func(self, request, context, request_id, user_id)
    return wrapper

def admin_auth_middleware(func):
    @wraps(func)
    async def wrapper(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        metadata = dict(context.invocation_metadata())
        token = metadata.get('authorization')
        if not token:
            logger.error("No authorization token provided")
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Authorization token required")
            raise AuthenticationError("Authorization token required")
        try:
            payload = jwt.decode(token.replace("Bearer ", ""), settings.jwt_secret_key, algorithms=["HS256"])
            if payload.get('role') != 'admin':
                logger.error("User is not an admin", user_id=payload.get('user_id'))
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Admin access required")
                raise AuthenticationError("Admin access required")
        except jwt.InvalidTokenError as e:
            logger.error("Invalid JWT token", error=str(e))
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(f"Invalid JWT token: {str(e)}")
            raise AuthenticationError(f"Invalid JWT token: {str(e)}")
        return await func(self, request, context, request_id)
    return wrapper

def response_to_dict(response):
    if isinstance(response, user_pb2.UserResponse):
        return {
            "id": response.id,
            "name": response.name,
            "created_at": response.created_at,
            "role": response.role
        }
    elif isinstance(response, user_pb2.UserDeletedResponse):
        return {"success": response.success}
    return response.__dict__

class AdminServiceGRPC(user_pb2_grpc.AdminServiceServicer):
    def __init__(self, container: AsyncContainer):
        self.container = container
        self.logger = logger.bind(service="AdminServiceGRPC")

    async def _get_admin_service(self):
        return await self.container.get(AdminService)

    @log_execution_time
    @handle_grpc_exceptions
    @admin_auth_middleware
    async def CreateUser(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = CreateUserDTO(id=UUID(request.id), name=request.name, role=request.role)
        logger.info("Processing CreateUser", input_data=input_data.dict())
        admin_service = await self._get_admin_service()
        user = await admin_service.create_user(input_data, request_id)
        response = user_pb2.UserResponse(
            id=str(user.id),
            name=user.name,
            created_at=user.created_at.isoformat(),
            role=user.role
        )
        logger.info("CreateUser request completed", response=response_to_dict(response))
        return response

    @log_execution_time
    @handle_grpc_exceptions
    @admin_auth_middleware
    async def GetUser(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        try:
            input_data = UserIdDTO(id=UUID(request.id))
        except ValueError as e:
            logger.error("Invalid UUID format", id=request.id)
            raise InvalidInputError(f"Invalid UUID format: {request.id}")
        logger.info("Processing GetUser", input_data=input_data.dict())
        admin_service = await self._get_admin_service()
        user = await admin_service.get_user(input_data, request_id)
        response = user_pb2.UserResponse(
            id=str(user.id),
            name=user.name,
            created_at=user.created_at.isoformat(),
            role=user.role
        )
        logger.info("GetUser request completed", response=response_to_dict(response))
        return response

    @log_execution_time
    @handle_grpc_exceptions
    @admin_auth_middleware
    async def UpdateUser(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        try:
            user_id = UUID(request.id)
        except ValueError as e:
            logger.error("Invalid UUID format", id=request.id)
            raise InvalidInputError(f"Invalid UUID format: {request.id}")
        input_data = UpdateUserDTO(name=request.name)
        logger.info("Processing UpdateUser", input_data=input_data.dict(), user_id=str(user_id))
        admin_service = await self._get_admin_service()
        user = await admin_service.update_user(user_id, input_data, request_id)
        response = user_pb2.UserResponse(
            id=str(user.id),
            name=user.name,
            created_at=user.created_at.isoformat(),
            role=user.role
        )
        logger.info("UpdateUser request completed", response=response_to_dict(response))
        return response

    @log_execution_time
    @handle_grpc_exceptions
    @admin_auth_middleware
    async def DeleteUser(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        try:
            input_data = UserIdDTO(id=UUID(request.id))
        except ValueError as e:
            logger.error("Invalid UUID format", id=request.id)
            raise InvalidInputError(f"Invalid UUID format: {request.id}")
        logger.info("Processing DeleteUser", input_data=input_data.dict())
        admin_service = await self._get_admin_service()
        success = await admin_service.delete_user(input_data, request_id)
        response = user_pb2.UserDeletedResponse(success=success)
        logger.info("DeleteUser request completed", response=response_to_dict(response))
        return response

class UserServiceGRPC(user_pb2_grpc.UserServiceServicer):
    def __init__(self, container: AsyncContainer):
        self.container = container
        self.logger = logger.bind(service="UserServiceGRPC")

    async def _get_user_service(self):
        return await self.container.get(UserService)

    @log_execution_time
    @handle_grpc_exceptions
    @jwt_auth_middleware
    async def GetMyProfile(self, request, context, request_id: str, user_id: UUID):
        logger = self.logger.bind(request_id=request_id)
        input_data = UserIdDTO(id=user_id)
        logger.info("Processing GetMyProfile", input_data=input_data.dict())
        user_service = await self._get_user_service()
        user = await user_service.get_my_profile(input_data, request_id)
        response = user_pb2.UserResponse(
            id=str(user.id),
            name=user.name,
            created_at=user.created_at.isoformat(),
            role=user.role
        )
        logger.info("GetMyProfile request completed", response=response_to_dict(response))
        return response

    @log_execution_time
    @handle_grpc_exceptions
    @jwt_auth_middleware
    async def UpdateMyName(self, request, context, request_id: str, user_id: UUID):
        logger = self.logger.bind(request_id=request_id)
        input_data = UpdateNameDTO(name=request.name)
        logger.info("Processing UpdateMyName", input_data=input_data.dict(), user_id=str(user_id))
        user_service = await self._get_user_service()
        user = await user_service.update_my_name(user_id, input_data, request_id)
        response = user_pb2.UserResponse(
            id=str(user.id),
            name=user.name,
            created_at=user.created_at.isoformat(),
            role=user.role
        )
        logger.info("UpdateMyName request completed", response=response_to_dict(response))
        return response

async def serve():
    try:
        container = await get_container()
        async with container():
            server = aio_server()
            user_pb2_grpc.add_AdminServiceServicer_to_server(AdminServiceGRPC(container), server)
            user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceGRPC(container), server)
            reflection.enable_server_reflection(SERVICE_NAMES, server)
            server.add_insecure_port(f"[::]:{settings.grpc_port}")
            logger.info(f"Server started on [::]:{settings.grpc_port} with reflection")
            await server.start()
            await server.wait_for_termination()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")