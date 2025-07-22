from functools import wraps
import grpc
from structlog import get_logger
from pydantic_core import ValidationError
from domain.exceptions import AuthenticationError, InvalidInputError
from application.utils.logging_utils import generate_request_id

logger = get_logger(__name__)

def handle_grpc_exceptions(func):
    @wraps(func)
    async def wrapper(self, request, context, *args, **kwargs):
        request_id = kwargs.get('request_id', generate_request_id())
        logger_with_request = self.logger.bind(request_id=request_id)
        try:
            return await func(self, request, context, request_id=request_id)
        except ValidationError as e:
            logger_with_request.error(f"Validation error in {func.__name__}", error=str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            raise
        except InvalidInputError as e:
            logger_with_request.error(f"Invalid input in {func.__name__}", error=str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            raise
        except AuthenticationError as e:
            logger_with_request.error(f"Authentication error in {func.__name__}", error=str(e))
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(str(e))
            raise
        except Exception as e:
            logger_with_request.error(f"Unexpected error in {func.__name__}", error=str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise
    return wrapper