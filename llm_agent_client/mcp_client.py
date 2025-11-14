"""
MCP Client - rule-based tool routing (minimal config)
Only uses LLM_MODEL_NAME and LLM_MODEL_URL environment variables for informational purposes.
"""
import json
import logging
from typing import Dict, Any, Optional, List
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MCPClient:
    """Client that uses deterministic rule-based parsing to route queries to MCP tools"""

    def __init__(self, mcp_server_url: str = "http://localhost:8001"):
        self.mcp_server_url = mcp_server_url
        self.tools_cache: Optional[List[Dict[str, Any]]] = None
        self.product_profile = "common"
        # Minimal LLM metadata (not required for operation)
        self.llm_model: str = os.getenv("LLM_MODEL_NAME", "")
        self.llm_endpoint: str = os.getenv("LLM_MODEL_URL", "")

    # ------------------------------------------------------------------
    # Tool listing / calling
    # ------------------------------------------------------------------
    def get_available_tools(self) -> List[Dict[str, Any]]:
        if self.tools_cache:
            return self.tools_cache
        try:
            response = requests.get(
                f"{self.mcp_server_url}/tools",
                headers={"Product-Profile": self.product_profile},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            self.tools_cache = data.get('tools', [])
            return self.tools_cache
        except Exception as e:
            logger.error(f"Failed to fetch tools: {e}")
            return []

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{self.mcp_server_url}/tools/call",
                json={"tool_name": tool_name, "arguments": arguments},
                headers={"Product-Profile": self.product_profile},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"status": "error", "error": str(e)}

    def build_tools_description(self) -> str:
        tools = self.get_available_tools()
        if not tools:
            return "No tools available."
        description = "You have access to the following CVE database tools:\n\n"
        for tool in tools:
            name = tool.get('name', 'Unknown')
            desc = tool.get('description', 'No description')
            schema = tool.get('input_schema', {})
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            description += f"**{name}**\nDescription: {desc}\nParameters:\n"
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '')
                is_required = param_name in required
                req_marker = " (required)" if is_required else " (optional)"
                if 'enum' in param_info:
                    enum_values = ', '.join(param_info['enum'])
                    description += f"  - {param_name} ({param_type}){req_marker}: {param_desc}\n    Options: {enum_values}\n"
                else:
                    description += f"  - {param_name} ({param_type}){req_marker}: {param_desc}\n"
            description += "\n"
        return description

    # ------------------------------------------------------------------
    # Rule-based fallback decision logic
    # ------------------------------------------------------------------
    def _rule_based_decision(self, query: str) -> Dict[str, Any]:
        q = query.lower().strip()
        tool = "search_cves_by_keyword"
        arguments: Dict[str, Any] = {"keyword": query, "limit": 10, "output_format": "list"}
        reasoning = "Generic keyword search fallback"

        # CVE ID lookup
        cve_match = re.search(r"cve-\d{4}-\d{4,7}", q)
        if cve_match:
            tool = "get_cve_details"
            arguments = {"cve_id": cve_match.group(0).upper(), "output_format": "detailed"}
            reasoning = "Detected specific CVE identifier"
            return {"tool": tool, "arguments": arguments, "reasoning": reasoning}

        # Severity mapping
        severity_map = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW"
        }
        for word, sev in severity_map.items():
            if re.search(fr"\b{word}\b", q):
                tool = "search_cves_by_severity"
                arguments = {"severity": sev, "limit": 10, "output_format": "list"}
                reasoning = f"Detected severity term '{word}'"
                return {"tool": tool, "arguments": arguments, "reasoning": reasoning}

        # Recent
        if any(w in q for w in ["recent", "latest", "newly", "new"]):
            tool = "list_recent_cves"
            arguments = {"limit": 10, "output_format": "list"}
            reasoning = "Detected recency intent"
            return {"tool": tool, "arguments": arguments, "reasoning": reasoning}

        # Exploit maturity
        maturity_options = ["functional", "proof of concept", "unproven", "high"]
        for m in maturity_options:
            if m in q:
                tool = "search_cves_by_exploit_maturity"
                arguments = {"maturity": m.title(), "limit": 10, "output_format": "list"}
                reasoning = f"Detected exploit maturity term '{m}'"
                return {"tool": tool, "arguments": arguments, "reasoning": reasoning}

        # CVSS range (e.g., score 7 to 9, 7-9, between 5 and 7)
        range_match = re.search(r"(\d\.?\d?)\s*(?:-|to|and)\s*(\d\.?\d?)", q)
        if ("score" in q or "cvss" in q) and range_match:
            try:
                min_score = float(range_match.group(1))
                max_score = float(range_match.group(2))
                if 0 <= min_score <= 10 and 0 <= max_score <= 10 and min_score <= max_score:
                    tool = "search_cves_by_cvss_score"
                    arguments = {"min_score": min_score, "max_score": max_score, "limit": 10, "output_format": "list"}
                    reasoning = "Detected CVSS score range"
                    return {"tool": tool, "arguments": arguments, "reasoning": reasoning}
            except Exception:
                pass

        # Short keyword improvement: if query is one word like 'apache'
        if len(q.split()) == 1:
            reasoning = "Single keyword search"
            return {"tool": tool, "arguments": arguments, "reasoning": reasoning}

        return {"tool": tool, "arguments": arguments, "reasoning": reasoning}

    # ------------------------------------------------------------------
    # HTML sanitization (unchanged)
    # ------------------------------------------------------------------
    def sanitize_html(self, html: str) -> str:
        if not html:
            return html
        cleaned_lines = []
        for line in html.splitlines():
            cleaned_lines.append(line.lstrip() if line.strip() else "")
        return "\n".join(cleaned_lines)

    # ------------------------------------------------------------------
    # Query processing
    # ------------------------------------------------------------------
    async def process_query(self, user_query: str) -> str:
        decision = self._rule_based_decision(user_query)
        tool_name = decision.get('tool')
        arguments = decision.get('arguments', {})
        reasoning = decision.get('reasoning', '')

        logger.info(f"Decision tool={tool_name} args={arguments} reasoning={reasoning}")

        result = self.call_mcp_tool(tool_name, arguments)

        if result.get('status') == 'success':
            tool_result = result.get('result', {})
            if tool_result.get('status') == 'success':
                rendered = tool_result.get('rendered')
                count = tool_result.get('count')
                response_text = f"**🤖 Query Analysis:** {reasoning}\n\n"
                if count is not None:
                    response_text += f"**✅ Found {count} CVE(s)**\n\n"
                if rendered:
                    rendered = self.sanitize_html(rendered)
                    response_text += rendered
                else:
                    data = tool_result.get('data')
                    if data:
                        response_text += f"```json\n{json.dumps(data, indent=2)}\n```"
                    else:
                        response_text += "No data available."
                return response_text
            else:
                error_msg = tool_result.get('message', 'Unknown error')
                return f"**❌ Error:** {error_msg}"
        else:
            error = result.get('error', 'Unknown error')
            return f"**❌ Server error:** {error}"

    # ------------------------------------------------------------------
    # Connection helpers (unchanged external API)
    # ------------------------------------------------------------------
    def check_connection(self) -> bool:
        try:
            response = requests.get(f"{self.mcp_server_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def setup_agent(self) -> bool:
        connected = self.check_connection()
        if connected:
            self.get_available_tools()
        return connected

    def list_tools(self) -> List[Dict[str, Any]]:
        return self.get_available_tools()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], product_profile: Optional[str] = None) -> Dict[str, Any]:
        if product_profile:
            self.product_profile = product_profile
        return self.call_mcp_tool(tool_name, arguments)

    def disconnect(self):
        pass
