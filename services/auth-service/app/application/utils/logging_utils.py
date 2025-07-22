import time
from functools import wraps
from typing import Callable, TypeVar, Any
from uuid import uuid4
from structlog import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

def generate_request_id() -> str:
    return str(uuid4())

def filter_sensitive_data(data: dict) -> dict:
    return {k: v for k, v in data.items() if k not in ["password", "new_password", "auth_data"]}

def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        start_time = time.perf_counter()
        request_id = kwargs.get('request_id', generate_request_id())
        logger_with_request = logger.bind(request_id=request_id)
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger_with_request.info(
                f"Function {func.__name__} executed successfully",
                duration_ms=f"{duration_ms:.2f}",
                func_name=func.__name__,
                module=func.__module__,
            )
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger_with_request.error(
                f"Function {func.__name__} failed",
                duration_ms=f"{duration_ms:.2f}",
                func_name=func.__name__,
                module=func.__module__,
                error=str(e),
            )
            raise
    return async_wrapper