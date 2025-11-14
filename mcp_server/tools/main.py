import asyncio
import os
import logging

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from mcp_server.middleware.context import ContextMiddleware
from mcp_server.middleware.role_authorization import RoleAuthorizationMiddleware
from mcp_server.tools import load_tools
import uvicorn
from uvicorn.config import Config


logger: logging.Logger = logging.getLogger(__name__)

# Load tools from mcp_server.tools package
load_tools()

# Create the FastAPI instance
app = FastAPI(title="MCPDateServer")

# Register middleware with the MCP server
middleware = [
    Middleware(RoleAuthorizationMiddleware),
    Middleware(ContextMiddleware),
]

app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)

# Setup logging for the server
service_ver.set("mcp_server")
setup_logging()

# Import the tools to be registered on the FastAPI app
from mcp_server.tools import *


def run_mcp_server() -> None:
    """Start the MCP server with all registered toolkits."""
    logger.info("Starting MCP server...")

    # Create the Uvicorn configuration
    config = Config(
        app=app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        ssl_keyfile=os.getenv("SSL_KEYFILE"),
        ssl_certfile=os.getenv("SSL_CERTFILE"),
    )

    # Start the Uvicorn server
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


if __name__ == "__main__":
    run_mcp_server()