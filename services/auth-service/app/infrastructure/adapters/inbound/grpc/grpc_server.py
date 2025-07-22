import grpc
import asyncio
from grpc.aio import server as aio_server
from grpc_reflection.v1alpha import reflection
from dishka import AsyncContainer
from config import settings
from infrastructure.di.container import get_container
from application.auth_service_impl import AuthService
from application.dto.auth_dto import RegisterDTO, LoginDTO, GoogleLoginDTO, TelegramLoginDTO, AuthResponseDTO, RefreshTokenDTO, RequestPasswordResetDTO, ResetPasswordDTO
from application.utils.logging_utils import generate_request_id, log_execution_time, filter_sensitive_data
from application.utils.grpc_utils import handle_grpc_exceptions
from . import auth_pb2_grpc, auth_pb2
from structlog import get_logger

logger = get_logger(__name__)

SERVICE_NAMES = (
    auth_pb2.DESCRIPTOR.services_by_name['AuthService'].full_name,
    reflection.SERVICE_NAME,
)

class AuthServiceGRPC(auth_pb2_grpc.AuthServiceServicer):
    def __init__(self, container: AsyncContainer):
        self.container = container
        self.logger = logger.bind(service="AuthServiceGRPC")

    async def _get_auth_service(self):
        return await self.container.get(AuthService)

    @log_execution_time
    @handle_grpc_exceptions
    async def Register(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = RegisterDTO(email=request.email, name=request.name, password=request.password)
        logger.info("Processing Register", input_data=filter_sensitive_data(input_data.dict()))
        auth_service = await self._get_auth_service()
        response_dto = await auth_service.register(input_data, request_id)
        response = auth_pb2.AuthResponse(
            access_token=response_dto.access_token,
            refresh_token=response_dto.refresh_token
        )
        logger.info("Register request completed", response=response.__dict__)
        return response

    @log_execution_time
    @handle_grpc_exceptions
    async def Login(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = LoginDTO(email=request.email, password=request.password)
        logger.info("Processing Login", input_data=filter_sensitive_data(input_data.dict()))
        auth_service = await self._get_auth_service()
        response_dto = await auth_service.login(input_data, request_id)
        response = auth_pb2.AuthResponse(
            access_token=response_dto.access_token,
            refresh_token=response_dto.refresh_token
        )
        logger.info("Login request completed", response=response.__dict__)
        return response

    @log_execution_time
    @handle_grpc_exceptions
    async def LoginWithGoogle(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = GoogleLoginDTO(id_token=request.id_token)
        logger.info("Processing LoginWithGoogle", input_data=filter_sensitive_data(input_data.dict()))
        auth_service = await self._get_auth_service()
        response_dto = await auth_service.login_with_google(input_data, request_id)
        response = auth_pb2.AuthResponse(
            access_token=response_dto.access_token,
            refresh_token=response_dto.refresh_token
        )
        logger.info("LoginWithGoogle request completed", response=response.__dict__)
        return response

    @log_execution_time
    @handle_grpc_exceptions
    async def LoginWithTelegram(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = TelegramLoginDTO(telegram_id=request.telegram_id, auth_data=request.auth_data)
        logger.info("Processing LoginWithTelegram", input_data=filter_sensitive_data(input_data.dict()))
        auth_service = await self._get_auth_service()
        response_dto = await auth_service.login_with_telegram(input_data, request_id)
        response = auth_pb2.AuthResponse(
            access_token=response_dto.access_token,
            refresh_token=response_dto.refresh_token
        )
        logger.info("LoginWithTelegram request completed", response=response.__dict__)
        return response

    @log_execution_time
    @handle_grpc_exceptions
    async def RefreshToken(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = RefreshTokenDTO(refresh_token=request.refresh_token)
        logger.info("Processing RefreshToken", input_data=input_data.dict())
        auth_service = await self._get_auth_service()
        response_dto = await auth_service.refresh_token(input_data, request_id)
        response = auth_pb2.AuthResponse(
            access_token=response_dto.access_token,
            refresh_token=response_dto.refresh_token
        )
        logger.info("RefreshToken request completed", response=response.__dict__)
        return response

    @log_execution_time
    @handle_grpc_exceptions
    async def RequestPasswordReset(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = RequestPasswordResetDTO(email=request.email)
        logger.info("Processing RequestPasswordReset", input_data=input_data.dict())
        auth_service = await self._get_auth_service()
        success = await auth_service.request_password_reset(input_data, request_id)
        response = auth_pb2.RequestPasswordResetResponse(success=success)
        logger.info("RequestPasswordReset completed", response=response.__dict__)
        return response

    @log_execution_time
    @handle_grpc_exceptions
    async def ResetPassword(self, request, context, request_id: str):
        logger = self.logger.bind(request_id=request_id)
        input_data = ResetPasswordDTO(reset_token=request.reset_token, new_password=request.new_password)
        logger.info("Processing ResetPassword", input_data=filter_sensitive_data(input_data.dict()))
        auth_service = await self._get_auth_service()
        success = await auth_service.reset_password(input_data, request_id)
        response = auth_pb2.ResetPasswordResponse(success=success)
        logger.info("ResetPassword completed", response=response.__dict__)
        return response

async def serve():
    try:
        container = await get_container()
        async with container():
            server = aio_server()
            auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceGRPC(container), server)
            reflection.enable_server_reflection(SERVICE_NAMES, server)
            server.add_insecure_port(f"[::]:{settings.grpc_port}")
            logger.info(f"Server started on [::]:{settings.grpc_port} with reflection")
            await server.start()
            await server.wait_for_termination()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")