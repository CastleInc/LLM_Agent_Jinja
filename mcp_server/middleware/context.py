import logging
from typing import Any, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger: logging.Logger = logging.getLogger(__name__)

# Context variables
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='default-correlation-id')
user_id_var: ContextVar[str] = ContextVar('user_id', default='default-user-id')


class ContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set correlation_id and user_id from request headers."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Intercept the request and set context variables."""
        try:
            # Extract correlation_id and user_id from headers
            correlation_id = request.headers.get(
                "Correlation-ID",
                request.headers.get("X-Correlation-ID", "default-correlation-id")
            )
            user_id = request.headers.get(
                "User-ID",
                request.headers.get("X-User-ID", "default-user-id")
            )

            # Set the values in the context variables
            correlation_id_var.set(correlation_id)
            user_id_var.set(user_id)

            logger.info(
                f"Request context - correlation_id: {correlation_id}, user_id: {user_id}"
            )

        except Exception as e:
            logger.error(f"Failed to set context variables: {e}")

        # Continue processing the request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id_var.get()

        return response