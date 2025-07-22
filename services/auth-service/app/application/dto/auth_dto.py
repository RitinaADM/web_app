from pydantic import BaseModel, EmailStr, Field

class RegisterDTO(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

class LoginDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class GoogleLoginDTO(BaseModel):
    id_token: str

class TelegramLoginDTO(BaseModel):
    telegram_id: str
    auth_data: str

class AuthResponseDTO(BaseModel):
    access_token: str
    refresh_token: str

class RefreshTokenDTO(BaseModel):
    refresh_token: str

class RequestPasswordResetDTO(BaseModel):
    email: EmailStr

class ResetPasswordDTO(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)