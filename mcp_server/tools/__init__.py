"""Tools package"""
from mcp_server.tools.registry import get_tool_registry, MCPToolRegistry

# Get global registry instance
mcp = get_tool_registry()

__all__ = ['mcp', 'get_tool_registry', 'MCPToolRegistry']


def load_tools():
    """Load all tool modules"""
    # Import tool modules to trigger registration
    from mcp_server.tools import cve_tools
    import logging
    logger = logging.getLogger(__name__)
    logger.info("CVE tools loaded")

