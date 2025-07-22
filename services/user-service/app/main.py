import structlog
import asyncio
from infrastructure.adapters.inbound.grpc.grpc_server import serve
import logging

# Настраиваем стандартный Python-логгер для вывода в stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # structlog будет форматировать сообщение в JSON
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

if __name__ == "__main__":
    asyncio.run(serve())