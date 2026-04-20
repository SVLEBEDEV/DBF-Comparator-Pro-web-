import contextvars
import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response

from app.core.config import Settings


request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
        force=True,
    )
    root = logging.getLogger()
    request_filter = RequestIdFilter()
    if not any(isinstance(existing, RequestIdFilter) for existing in root.filters):
        root.addFilter(request_filter)
    for handler in root.handlers:
        if not any(isinstance(existing, RequestIdFilter) for existing in handler.filters):
            handler.addFilter(request_filter)


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Response],
    *,
    header_name: str,
) -> Response:
    request_id = request.headers.get(header_name) or str(uuid.uuid4())
    token = request_id_ctx.set(request_id)
    started_at = time.perf_counter()
    logger = logging.getLogger("app.http")

    try:
        response = await call_next(request)
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info("%s %s completed in %sms", request.method, request.url.path, duration_ms)
        request_id_ctx.reset(token)

    response.headers[header_name] = request_id
    return response
