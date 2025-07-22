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
    """Провайдер зависимостей для приложения."""

    @provide(scope=Scope.APP)
    async def get_mongo_client(self) -> AsyncMongoClient:
        client = AsyncMongoClient(settings.mongo_uri, uuidRepresentation=settings.mongo_uuid_representation)
        logger.info("Клиент MongoDB инициализирован")
        return client

    @provide(scope=Scope.APP)
    async def get_mongo_collection(self, client: AsyncMongoClient) -> Collection:
        db = client[settings.mongo_db]
        collection = db["users"]
        # Удаляем создание индекса для _id, так как он создается автоматически
        await collection.create_index("email", unique=True)
        logger.info("Коллекция MongoDB инициализирована")
        return collection

    @provide(scope=Scope.APP)
    async def get_redis_client(self) -> Redis:
        client = Redis.from_url(settings.redis_uri, decode_responses=True)
        logger.info("Клиент Redis инициализирован")
        return client

    @provide(scope=Scope.APP)
    async def get_cache_repository(self, redis_client: Redis) -> CachePort:
        logger.info("Репозиторий кэша Redis инициализирован")
        return RedisCacheRepository(redis_client)

    @provide(scope=Scope.APP)
    async def get_user_repository(self, collection: Collection, cache: CachePort) -> UserRepositoryPort:
        logger.info("Репозиторий пользователей инициализирован")
        return MongoUserRepository(collection, cache)

    @provide(scope=Scope.APP)
    async def get_user_service(self, repo: UserRepositoryPort) -> UserService:
        logger.info("Сервис пользователей инициализирован")
        return UserService(repo, settings.jwt_secret_key)

    @provide(scope=Scope.APP)
    async def get_admin_service(self, repo: UserRepositoryPort) -> AdminService:
        logger.info("Админский сервис инициализирован")
        return AdminService(repo)

async def get_container() -> AsyncContainer:
    container = make_async_container(AppProvider())
    logger.info("Асинхронный контейнер создан")
    return container