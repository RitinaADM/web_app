from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = Field(..., env="MONGO_URI")
    mongo_db: str = Field("auth_service", env="MONGO_DB")
    mongo_uuid_representation: str = Field("standard", env="MONGO_UUID_REPRESENTATION")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY", min_length=32)
    jwt_access_token_ttl: int = Field(3600, env="JWT_ACCESS_TOKEN_TTL")
    jwt_refresh_token_ttl: int = Field(604800, env="JWT_REFRESH_TOKEN_TTL")
    grpc_port: int = Field(50052, env="GRPC_PORT")
    redis_uri: str = Field("redis://redis:6379/0", env="REDIS_URI")
    redis_ttl: int = Field(604800, env="REDIS_TTL")
    user_service_grpc_host: str = Field("user-service:50051", env="USER_SERVICE_GRPC_HOST")
    notification_service_grpc_host: str = Field("notification-service:50053", env="NOTIFICATION_SERVICE_GRPC_HOST")
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()