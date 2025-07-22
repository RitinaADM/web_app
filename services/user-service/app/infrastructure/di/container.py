from dishka import Provider, Scope, provide, make_async_container, AsyncContainer
from pymongo import AsyncMongoClient
from pymongo.collection import Collection
from redis.asyncio import Redis
from infrastructure.adapters.outbound.mongo.user_repository import MongoUserRepository
from infrastructure.adapters.outbound.redis.cache_repository import RedisCacheRepository
from application.user_service_impl import UserService
from application.admin_service_impl import AdminService
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from domain.ports.outbound.cache_port import CachePort
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
        collection = db["users"]
        await collection.create_index("name")  # Добавляем индекс для поля name
        logger.info("MongoDB collection initialized")
        return collection

    @provide(scope=Scope.APP)
    async def get_redis_client(self) -> Redis:
        client = Redis.from_url(settings.redis_uri, decode_responses=True)
        logger.info("Redis client initialized")
        return client

    @provide(scope=Scope.APP)
    async def get_cache_repository(self, redis_client: Redis) -> CachePort:
        logger.info("Redis cache repository initialized")
        return RedisCacheRepository(redis_client)

    @provide(scope=Scope.APP)
    async def get_user_repository(self, collection: Collection, cache: CachePort) -> UserRepositoryPort:
        logger.info("User repository initialized")
        return MongoUserRepository(collection, cache)

    @provide(scope=Scope.APP)
    async def get_user_service(self, repo: UserRepositoryPort) -> UserService:
        logger.info("User service initialized")
        return UserService(repo)

    @provide(scope=Scope.APP)
    async def get_admin_service(self, repo: UserRepositoryPort) -> AdminService:
        logger.info("Admin service initialized")
        return AdminService(repo)

async def get_container() -> AsyncContainer:
    container = make_async_container(AppProvider())
    logger.info("Async container created")
    return container