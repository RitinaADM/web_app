import time
from functools import wraps
from typing import Callable, TypeVar, Any
from uuid import uuid4
from structlog import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

def generate_request_id() -> str:
    """Генерирует уникальный request_id."""
    return str(uuid4())

def filter_sensitive_data(data: dict) -> dict:
    """Фильтрует конфиденциальные данные, такие как пароли."""
    return {k: v for k, v in data.items() if k != "password"}

def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """Декоратор для логирования времени выполнения функции."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        start_time = time.perf_counter()
        request_id = kwargs.get('request_id', generate_request_id())  # Используем переданный request_id
        logger_with_request = logger.bind(request_id=request_id)
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger_with_request.info(
                f"Функция {func.__name__} выполнена успешно",
                duration_ms=f"{duration_ms:.2f}",
                func_name=func.__name__,
                module=func.__module__,
            )
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger_with_request.error(
                f"Функция {func.__name__} завершилась с ошибкой",
                duration_ms=f"{duration_ms:.2f}",
                func_name=func.__name__,
                module=func.__module__,
                error=str(e),
            )
            raise
    return async_wrapper