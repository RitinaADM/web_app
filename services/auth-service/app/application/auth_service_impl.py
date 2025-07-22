import bcrypt
import jwt
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Optional
from google.auth import jwt as google_jwt
from domain.ports.inbound.auth_service_port import AuthServicePort
from domain.ports.outbound.auth_repository_port import AuthRepositoryPort
from domain.ports.outbound.token_repository_port import TokenRepositoryPort
from domain.ports.outbound.user_service_client_port import UserServiceClientPort
from domain.models.auth_user import AuthUser
from domain.models.token import RefreshToken, ResetToken
from domain.exceptions import AuthenticationError, InvalidInputError
from application.dto.auth_dto import RegisterDTO, LoginDTO, AuthResponseDTO, RefreshTokenDTO, GoogleLoginDTO, TelegramLoginDTO, RequestPasswordResetDTO, ResetPasswordDTO
from application.utils.logging_utils import log_execution_time, filter_sensitive_data
from config import settings
from structlog import get_logger

logger = get_logger(__name__)

class AuthService(AuthServicePort):
    def __init__(self, auth_repo: AuthRepositoryPort, token_repo: TokenRepositoryPort, user_service_client: UserServiceClientPort):
        self.auth_repo = auth_repo
        self.token_repo = token_repo
        self.user_service_client = user_service_client
        self.secret_key = settings.jwt_secret_key
        self.access_ttl = settings.jwt_access_token_ttl
        self.refresh_ttl = settings.jwt_refresh_token_ttl
        self.google_client_id = settings.google_client_id
        self.logger = logger.bind(service="AuthService")

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def _generate_access_token(self, user_id: UUID, role: str) -> str:
        payload = {
            "user_id": str(user_id),
            "role": role,
            "exp": datetime.utcnow() + timedelta(seconds=self.access_ttl)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _generate_refresh_token(self, user_id: UUID) -> str:
        return str(uuid4())

    @log_execution_time
    async def register(self, register_dto: RegisterDTO, request_id: str) -> AuthResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Registering user", input_data=filter_sensitive_data(register_dto.dict()))
            existing_user = await self.auth_repo.get_by_email(register_dto.email, request_id)
            if existing_user:
                logger.error("Email already exists", email=register_dto.email)
                raise InvalidInputError(f"Email {register_dto.email} already exists")
            user_id = uuid4()
            role = "admin" if register_dto.email == "admin@example.com" else "user"
            auth_user = AuthUser(
                user_id=user_id,
                email=register_dto.email,
                hashed_password=self._hash_password(register_dto.password),
                login_methods=["email"],
                created_at=datetime.utcnow()
            )
            await self.auth_repo.create(auth_user, request_id)
            await self.user_service_client.create_user(user_id, register_dto.name, role, request_id)
            refresh_token = self._generate_refresh_token(user_id)
            await self.token_repo.store_refresh_token(
                RefreshToken(token=refresh_token, user_id=user_id),
                request_id
            )
            access_token = self._generate_access_token(user_id, role)
            response = AuthResponseDTO(access_token=access_token, refresh_token=refresh_token)
            logger.info("User registered successfully", user_id=str(user_id))
            return response
        except InvalidInputError as e:
            logger.error("Invalid input for registration", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in registration", error=str(e))
            raise RuntimeError(f"Unexpected error in registration: {str(e)}")

    @log_execution_time
    async def login(self, login_dto: LoginDTO, request_id: str) -> AuthResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Processing login", email=login_dto.email)
            auth_user = await self.auth_repo.get_by_email(login_dto.email, request_id)
            if not auth_user or not self._verify_password(login_dto.password, auth_user.hashed_password):
                logger.error("Invalid credentials", email=login_dto.email)
                raise AuthenticationError("Invalid email or password")
            user = await self.user_service_client.get_user_by_id(auth_user.user_id, request_id)
            if not user:
                logger.error("User profile not found", user_id=str(auth_user.user_id))
                raise AuthenticationError("User profile not found")
            refresh_token = self._generate_refresh_token(auth_user.user_id)
            await self.token_repo.store_refresh_token(
                RefreshToken(token=refresh_token, user_id=auth_user.user_id),
                request_id
            )
            access_token = self._generate_access_token(auth_user.user_id, user.role)
            response = AuthResponseDTO(access_token=access_token, refresh_token=refresh_token)
            logger.info("User logged in successfully", user_id=str(auth_user.user_id))
            return response
        except AuthenticationError as e:
            logger.error("Authentication failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in login", error=str(e))
            raise AuthenticationError(f"Unexpected error in login: {str(e)}")

    @log_execution_time
    async def login_with_google(self, google_dto: GoogleLoginDTO, request_id: str) -> AuthResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Processing Google login")
            decoded_token = google_jwt.decode(google_dto.id_token, verify=True, certs_url="https://www.googleapis.com/oauth2/v3/certs")
            if decoded_token["aud"] != self.google_client_id:
                logger.error("Invalid Google client ID")
                raise AuthenticationError("Invalid Google client ID")
            email = decoded_token["email"]
            auth_user = await self.auth_repo.get_by_email(email, request_id)
            if not auth_user:
                user_id = uuid4()
                auth_user = AuthUser(
                    user_id=user_id,
                    email=email,
                    hashed_password=None,
                    login_methods=["google"],
                    created_at=datetime.utcnow()
                )
                await self.auth_repo.create(auth_user, request_id)
                await self.user_service_client.create_user(user_id, decoded_token.get("name", "Google User"), "user", request_id)
            user = await self.user_service_client.get_user_by_id(auth_user.user_id, request_id)
            if not user:
                logger.error("User profile not found", user_id=str(auth_user.user_id))
                raise AuthenticationError("User profile not found")
            refresh_token = self._generate_refresh_token(auth_user.user_id)
            await self.token_repo.store_refresh_token(
                RefreshToken(token=refresh_token, user_id=auth_user.user_id),
                request_id
            )
            access_token = self._generate_access_token(auth_user.user_id, user.role)
            response = AuthResponseDTO(access_token=access_token, refresh_token=refresh_token)
            logger.info("Google login successful", user_id=str(auth_user.user_id))
            return response
        except Exception as e:
            logger.error("Unexpected error in Google login", error=str(e))
            raise AuthenticationError(f"Unexpected error in Google login: {str(e)}")

    @log_execution_time
    async def login_with_telegram(self, telegram_dto: TelegramLoginDTO, request_id: str) -> AuthResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Processing Telegram login", telegram_id=telegram_dto.telegram_id)
            auth_user = await self.auth_repo.get_by_telegram_id(telegram_dto.telegram_id, request_id)
            if not auth_user:
                user_id = uuid4()
                auth_user = AuthUser(
                    user_id=user_id,
                    email=None,
                    hashed_password=None,
                    login_methods=["telegram"],
                    telegram_id=telegram_dto.telegram_id,
                    created_at=datetime.utcnow()
                )
                await self.auth_repo.create(auth_user, request_id)
                await self.user_service_client.create_user(user_id, "Telegram User", "user", request_id)
            user = await self.user_service_client.get_user_by_id(auth_user.user_id, request_id)
            if not user:
                logger.error("User profile not found", user_id=str(auth_user.user_id))
                raise AuthenticationError("User profile not found")
            refresh_token = self._generate_refresh_token(auth_user.user_id)
            await self.token_repo.store_refresh_token(
                RefreshToken(token=refresh_token, user_id=auth_user.user_id),
                request_id
            )
            access_token = self._generate_access_token(auth_user.user_id, user.role)
            response = AuthResponseDTO(access_token=access_token, refresh_token=refresh_token)
            logger.info("Telegram login successful", user_id=str(auth_user.user_id))
            return response
        except Exception as e:
            logger.error("Unexpected error in Telegram login", error=str(e))
            raise AuthenticationError(f"Unexpected error in Telegram login: {str(e)}")

    @log_execution_time
    async def refresh_token(self, refresh_dto: RefreshTokenDTO, request_id: str) -> AuthResponseDTO:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Refreshing token")
            token = await self.token_repo.get_refresh_token(refresh_dto.refresh_token, request_id)
            if not token:
                logger.error("Invalid refresh token")
                raise AuthenticationError("Invalid refresh token")
            user = await self.user_service_client.get_user_by_id(token.user_id, request_id)
            if not user:
                logger.error("User not found for refresh token", user_id=str(token.user_id))
                raise AuthenticationError("User not found")
            new_refresh_token = self._generate_refresh_token(token.user_id)
            await self.token_repo.store_refresh_token(
                RefreshToken(token=new_refresh_token, user_id=token.user_id),
                request_id
            )
            await self.token_repo.delete_refresh_token(refresh_dto.refresh_token, request_id)
            access_token = self._generate_access_token(token.user_id, user.role)
            response = AuthResponseDTO(access_token=access_token, refresh_token=new_refresh_token)
            logger.info("Token refreshed successfully", user_id=str(token.user_id))
            return response
        except AuthenticationError as e:
            logger.error("Refresh token failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in refresh token", error=str(e))
            raise RuntimeError(f"Unexpected error in refresh token: {str(e)}")

    @log_execution_time
    async def request_password_reset(self, reset_dto: RequestPasswordResetDTO, request_id: str) -> bool:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Requesting password reset", email=reset_dto.email)
            auth_user = await self.auth_repo.get_by_email(reset_dto.email, request_id)
            if not auth_user:
                logger.warning("User not found for password reset", email=reset_dto.email)
                return False
            reset_token = str(uuid4())
            await self.token_repo.store_reset_token(
                ResetToken(token=reset_token, user_id=auth_user.user_id, ttl=3600),
                request_id
            )
            logger.info("Password reset token generated, notification pending", user_id=str(auth_user.user_id))
            return True
        except Exception as e:
            logger.error("Unexpected error in password reset request", error=str(e))
            raise RuntimeError(f"Unexpected error in password reset request: {str(e)}")

    @log_execution_time
    async def reset_password(self, reset_dto: ResetPasswordDTO, request_id: str) -> bool:
        logger = self.logger.bind(request_id=request_id)
        try:
            logger.info("Resetting password")
            token = await self.token_repo.get_reset_token(reset_dto.reset_token, request_id)
            if not token:
                logger.error("Invalid reset token")
                raise AuthenticationError("Invalid reset token")
            auth_user = await self.auth_repo.get_by_id(token.user_id, request_id)
            if not auth_user:
                logger.error("User not found for reset token", user_id=str(token.user_id))
                raise AuthenticationError("User not found")
            auth_user.set_hashed_password(self._hash_password(reset_dto.new_password))
            await self.auth_repo.update(auth_user, request_id)
            await self.token_repo.delete_reset_token(reset_dto.reset_token, request_id)
            logger.info("Password reset successfully", user_id=str(token.user_id))
            return True
        except AuthenticationError as e:
            logger.error("Reset password failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in reset password", error=str(e))
            raise RuntimeError(f"Unexpected error in reset password: {str(e)}")