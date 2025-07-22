from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class CreateUserDTO(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(user|admin)$")

class UpdateUserDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class UpdateNameDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class UserIdDTO(BaseModel):
    id: UUID

class UserResponseDTO(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    role: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            UUID: str,
            datetime: lambda dt: dt.isoformat()
        }