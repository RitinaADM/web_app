from dishka import Provider, Scope, provide, make_async_container, AsyncContainer
from pymongo import AsyncMongoClient
from pymongo.collection import Collection
from redis.asyncio import Redis
from infrastructure.adapters.outbound.mongo.auth_repository import MongoAuthRepository
from infrastructure.adapters.outbound.redis.token_repository import RedisTokenRepository
from infrastructure.adapters.outbound.grpc.user_service_client import UserServiceClient
from application.auth_service_impl import AuthService
from domain.ports.outbound.auth_repository_port import AuthRepositoryPort
from domain.ports.outbound.token_repository_port import TokenRepositoryPort
from domain.ports.outbound.user_service_client_port import UserServiceClientPort
from config import settings
from structlog import get_logger

logger = get_logger(__name__)

class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_mongo_client(self) -> AsyncMongoClient:
        client = AsyncMongoClient(settings.mongo_uri, uuidRepresentation=settings.mongo_uuid_representation)
        logger.info("MongoDB client initialized")
        return client

    @provide(scope=Scope.APP)
    async def get_mongo_collection(self, client: AsyncMongoClient) -> Collection:
        db = client[settings.mongo_db]
        collection = db["auth_users"]
        await collection.create_index("email", unique=True)
        await collection.create_index("telegram_id", unique=True)
        logger.info("MongoDB collection initialized")
        return collection

    @provide(scope=Scope.APP)
    async def get_redis_client(self) -> Redis:
        client = Redis.from_url(settings.redis_uri, decode_responses=True)
        logger.info("Redis client initialized")
        return client

    @provide(scope=Scope.APP)
    async def get_auth_repository(self, collection: Collection) -> AuthRepositoryPort:
        logger.info("Auth repository initialized")
        return MongoAuthRepository(collection)

    @provide(scope=Scope.APP)
    async def get_token_repository(self, redis_client: Redis) -> TokenRepositoryPort:
        logger.info("Token repository initialized")
        return RedisTokenRepository(redis_client)

    @provide(scope=Scope.APP)
    async def get_user_service_client(self) -> UserServiceClientPort:
        logger.info("User service client initialized")
        return UserServiceClient()

    @provide(scope=Scope.APP)
    async def get_auth_service(self, auth_repo: AuthRepositoryPort, token_repo: TokenRepositoryPort, user_service_client: UserServiceClientPort) -> AuthService:
        logger.info("Auth service initialized")
        return AuthService(auth_repo, token_repo, user_service_client)

async def get_container() -> AsyncContainer:
    container = make_async_container(AppProvider())
    logger.info("Async container created")
    return container