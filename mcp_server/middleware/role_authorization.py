import logging
from typing import Any, Callable, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from mcp_server.models import ProductProfile

logger: logging.Logger = logging.getLogger(__name__)


class RoleAuthorizationMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce role-based access control on tools."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Intercept requests and enforce role-based permissions."""

        # Extract product_profile from headers
        try:
            product_profile_str = request.headers.get("Product-Profile", "common")
            product_profile = ProductProfile.from_code(product_profile_str)

            # Store in request state for use in endpoints
            request.state.product_profile = product_profile

            logger.info(f"Request authorized for product profile: {product_profile}")

        except Exception as e:
            logger.error(f"Error in role authorization: {e}")
            request.state.product_profile = ProductProfile.COMMON

        # Continue processing the request
        response = await call_next(request)
        return response
