from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class CreateUserDTO(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

class UpdateUserDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

class UpdateNameDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class LoginDTO(BaseModel):
    email: EmailStr
    password: str

class UserIdDTO(BaseModel):
    id: UUID

class UserResponseDTO(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    created_at: datetime
    role: str = "user"  # Добавляем поле role

    class Config:
        arbitrary_types_allowed = True  # Для поддержки UUID и datetime
        json_encoders = {
            UUID: str,  # Преобразуем UUID в строку
            datetime: lambda dt: dt.isoformat()  # Преобразуем datetime в ISO 8601
        }