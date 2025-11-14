"""
MCP Server - FastAPI Application
Production-ready server with middleware, logging, and tool registration
"""
import asyncio
import os
import logging
import sys

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Add parent directory to path for mongo_service import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.middleware import ContextMiddleware, RoleAuthorizationMiddleware
from mcp_server.tools import load_tools, get_tool_registry
from mcp_server.models import ProductProfile
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: logging.Logger = logging.getLogger(__name__)

# Load tools from mcp_server.tools package
logger.info("Loading MCP tools...")
load_tools()

# Create the FastAPI instance with enhanced documentation
app = FastAPI(
    title="CVE MCP Server API",
    description="""
    ## Model Context Protocol Server for CVE Database
    
    Query and retrieve CVE vulnerability information with templated outputs.
    
    ### Features
    - 🔍 CVE Lookup by ID
    - 📊 Search by Severity, Exploit Maturity, Keywords
    - 📈 Advanced CVSS Score Range Queries
    - 🎨 Multiple Output Formats (detailed, summary, list, markdown, json)
    - 🔐 Role-Based Access Control (RBAC)
    
    ### Authentication
    Use the `Product-Profile` header to specify access level:
    - `common` - Basic access (most tools)
    - `premium` - Advanced features (CVSS range queries)
    - `admin` - Full access
    
    ### Example Usage
    ```bash
    curl -X POST http://localhost:8001/tools/call \\
      -H "Content-Type: application/json" \\
      -H "Product-Profile: common" \\
      -d '{
        "tool_name": "get_cve_details",
        "arguments": {"cve_id": "CVE-2021-44228", "output_format": "detailed"}
      }'
    ```
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "Tools",
            "description": "CVE tool discovery and execution"
        },
        {
            "name": "CVE Lookup",
            "description": "Retrieve specific CVE details"
        },
        {
            "name": "CVE Search",
            "description": "Search and filter CVE database"
        }
    ]
)

# Register middleware
app.add_middleware(ContextMiddleware)
app.add_middleware(RoleAuthorizationMiddleware)

# Get tool registry
tool_registry = get_tool_registry()


# Request/Response models
class ToolCallRequest(BaseModel):
    """Request model for tool execution"""
    tool_name: str
    arguments: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "tool_name": "get_cve_details",
                    "arguments": {
                        "cve_id": "CVE-2021-44228",
                        "output_format": "detailed"
                    }
                },
                {
                    "tool_name": "search_cves_by_severity",
                    "arguments": {
                        "severity": "CRITICAL",
                        "limit": 10,
                        "output_format": "list"
                    }
                },
                {
                    "tool_name": "search_cves_by_keyword",
                    "arguments": {
                        "keyword": "SQL injection",
                        "limit": 5,
                        "output_format": "list"
                    }
                }
            ]
        }


class ToolCallResponse(BaseModel):
    """Response model for tool execution"""
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": "success",
                    "result": {
                        "status": "success",
                        "data": {
                            "cve_number": "CVE-2021-44228",
                            "cve_title": "Apache Log4j Remote Code Execution",
                            "severity": "CRITICAL",
                            "cvss_score": 10.0
                        },
                        "rendered": "<div class='cve-report'>...</div>",
                        "format": "detailed"
                    }
                }
            ]
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CVE MCP Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    from mongo_service.connection import get_mongo_connection

    mongo_conn = get_mongo_connection()
    is_db_connected = mongo_conn.is_connected

    return {
        "status": "healthy" if is_db_connected else "degraded",
        "database_connected": is_db_connected,
        "tools_loaded": len(tool_registry.list_tools())
    }


@app.get("/tools", tags=["Tools"])
async def list_tools(request: Request):
    """List available tools based on product profile"""
    try:
        # Get product profile from request state (set by middleware)
        product_profile = getattr(request.state, 'product_profile', ProductProfile.COMMON)

        # Get tools for this profile
        tools = tool_registry.list_tools(product_profile)

        return {
            "status": "success",
            "product_profile": product_profile.value,
            "count": len(tools),
            "tools": [tool.to_dict() for tool in tools]
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/call", response_model=ToolCallResponse, tags=["Tools"])
async def call_tool(
    tool_request: ToolCallRequest,
    product_profile: str = Header(default="common", description="RBAC profile: common, premium, or admin")
):
    """
    Execute a CVE tool with specified arguments

    **Product-Profile Header Options:**
    - `common` - Basic access (CVE lookup, severity/keyword search)
    - `premium` - Advanced features (CVSS score range queries)
    - `admin` - Full access to all tools
    """
    try:
        logger.info(f"Calling tool: {tool_request.tool_name} with args: {tool_request.arguments}")

        # Convert string profile to enum
        try:
            profile_enum = ProductProfile.from_code(product_profile)
        except:
            profile_enum = ProductProfile.COMMON

        # Get the tool
        tool = tool_registry.get_tool(tool_request.tool_name)

        if tool is None:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_request.tool_name}' not found")

        # Check if user has access to this tool
        if profile_enum not in tool.product_profiles and profile_enum != ProductProfile.ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Tool requires one of: {[p.value for p in tool.product_profiles]}"
            )

        # Execute the tool
        result = await tool.execute(**tool_request.arguments)

        logger.info(f"Tool {tool_request.tool_name} executed successfully")

        return ToolCallResponse(
            status="success",
            result=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool {tool_request.tool_name}: {e}", exc_info=True)
        return ToolCallResponse(
            status="error",
            error=str(e)
        )


@app.get("/tools/{tool_name}", tags=["Tools"])
async def get_tool_info(tool_name: str, request: Request):
    """Get information about a specific tool"""
    product_profile = getattr(request.state, 'product_profile', ProductProfile.COMMON)

    tool = tool_registry.get_tool(tool_name)

    if tool is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # Check access
    if product_profile not in tool.product_profiles and product_profile != ProductProfile.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "status": "success",
        "tool": tool.to_dict()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


def run_mcp_server() -> None:
    """Start the MCP server with all registered toolkits."""
    logger.info("Starting CVE MCP Server...")

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")  # corrected default host
    port = int(os.getenv("PORT", 8001))

    logger.info(f"Server will start on {host}:{port}")
    logger.info(f"Registered tools: {len(tool_registry.list_tools())}")

    # Create the Uvicorn configuration
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        ssl_keyfile=os.getenv("SSL_KEYFILE") or None,
        ssl_certfile=os.getenv("SSL_CERTFILE") or None,
    )

    # Start the Uvicorn server
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


if __name__ == "__main__":
    run_mcp_server()