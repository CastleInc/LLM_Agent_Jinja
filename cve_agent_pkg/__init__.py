"""
CVE Agent Package
LLM-powered CVE intelligence system with Jinja templates and MCP tools
"""

__version__ = "2.0.0"
__author__ = "CVE Agent Team"

from cve_agent_pkg.core.agent import CVEAgent
from cve_agent_pkg.core.database import CVEDatabase
from cve_agent_pkg.core.renderer import CVETemplateRenderer
from cve_agent_pkg.mcp.tools import CVEMCPTools
from cve_agent_pkg.mcp.agent import MCPAgent

__all__ = [
    'CVEAgent',
    'CVEDatabase',
    'CVETemplateRenderer',
    'CVEMCPTools',
    'MCPAgent'
]
