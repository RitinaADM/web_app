from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = Field(..., env="MONGO_URI")
    mongo_db: str = Field("user_service", env="MONGO_DB")
    mongo_uuid_representation: str = Field("standard", env="MONGO_UUID_REPRESENTATION")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY", min_length=32)
    grpc_port: int = Field(50051, env="GRPC_PORT")
    redis_uri: str = Field("redis://redis:6379/0", env="REDIS_URI")  # Добавляем Redis URI
    redis_ttl: int = Field(3600, env="REDIS_TTL")  # Время жизни кэша в секундах (1 час)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()