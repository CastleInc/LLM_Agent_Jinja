"""
MCP Tool Registry and Decorator
"""
import logging
from typing import Dict, List, Any, Callable, Optional
from functools import wraps
from mcp_server.models import ProductProfile

logger = logging.getLogger(__name__)


class Tool:
    """MCP Tool definition"""

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        input_schema: Dict[str, Any],
        product_profiles: Optional[List[ProductProfile]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.func = func
        self.description = description
        self.input_schema = input_schema
        self.product_profiles = product_profiles or [ProductProfile.COMMON]
        self.metadata = metadata or {}

    async def execute(self, **kwargs) -> Any:
        """Execute the tool function"""
        try:
            result = self.func(**kwargs)
            # Handle async functions
            if hasattr(result, '__await__'):
                result = await result
            return result
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "product_profiles": [p.value for p in self.product_profiles],
            "metadata": self.metadata
        }


class MCPToolRegistry:
    """Registry for MCP tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        input_schema: Dict[str, Any],
        product_profiles: Optional[List[ProductProfile]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a tool"""
        tool = Tool(name, func, description, input_schema, product_profiles, metadata)
        self._tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self, product_profile: Optional[ProductProfile] = None) -> List[Tool]:
        """List all tools, optionally filtered by product profile"""
        if product_profile is None or product_profile == ProductProfile.ADMIN:
            return list(self._tools.values())

        # Filter by product profile
        filtered = []
        for tool in self._tools.values():
            if product_profile in tool.product_profiles:
                filtered.append(tool)

        return filtered

    def tool(
        self,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        product_profiles: Optional[List[ProductProfile]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Decorator to register a function as a tool"""
        def decorator(func: Callable) -> Callable:
            tool_name = func.__name__
            tool_description = description or func.__doc__ or f"Tool: {tool_name}"

            # Build input schema from function signature if not provided
            if input_schema is None:
                import inspect
                sig = inspect.signature(func)
                schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

                for param_name, param in sig.parameters.items():
                    param_type = "string"  # Default type
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"

                    schema["properties"][param_name] = {"type": param_type}

                    if param.default == inspect.Parameter.empty:
                        schema["required"].append(param_name)

                tool_input_schema = schema
            else:
                tool_input_schema = input_schema

            # Register the tool
            self.register_tool(
                tool_name,
                func,
                tool_description,
                tool_input_schema,
                product_profiles,
                metadata
            )

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator


# Global tool registry
_tool_registry = MCPToolRegistry()


def get_tool_registry() -> MCPToolRegistry:
    """Get global tool registry"""
    return _tool_registry

