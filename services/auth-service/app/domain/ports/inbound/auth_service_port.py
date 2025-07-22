from abc import ABC, abstractmethod
from application.dto.auth_dto import RegisterDTO, LoginDTO, GoogleLoginDTO, TelegramLoginDTO, AuthResponseDTO, RefreshTokenDTO, RequestPasswordResetDTO, ResetPasswordDTO

class AuthServicePort(ABC):
    @abstractmethod
    async def register(self, register_dto: RegisterDTO, request_id: str) -> AuthResponseDTO:
        pass

    @abstractmethod
    async def login(self, login_dto: LoginDTO, request_id: str) -> AuthResponseDTO:
        pass

    @abstractmethod
    async def login_with_google(self, google_dto: GoogleLoginDTO, request_id: str) -> AuthResponseDTO:
        pass

    @abstractmethod
    async def login_with_telegram(self, telegram_dto: TelegramLoginDTO, request_id: str) -> AuthResponseDTO:
        pass

    @abstractmethod
    async def refresh_token(self, refresh_dto: RefreshTokenDTO, request_id: str) -> AuthResponseDTO:
        pass

    @abstractmethod
    async def request_password_reset(self, reset_dto: RequestPasswordResetDTO, request_id: str) -> bool:
        pass

    @abstractmethod
    async def reset_password(self, reset_dto: ResetPasswordDTO, request_id: str) -> bool:
        pass