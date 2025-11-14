"""
MCP Client with LLM-based tool selection
Uses OpenAI to intelligently decide which CVE tool to call
"""
import json
import logging
from typing import Dict, Any, Optional, List
import requests
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import OpenAI with better error handling
try:
    from openai import OpenAI
except ImportError as e:
    logger.error(f"Failed to import OpenAI: {e}")
    raise ImportError("OpenAI library not installed. Run: pip install openai==1.54.0")


class MCPClient:
    """Client that uses LLM to intelligently route queries to MCP tools"""

    def __init__(self, mcp_server_url: str = "http://localhost:8001"):
        self.mcp_server_url = mcp_server_url

        # Initialize OpenAI client with error handling
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        try:
            self.openai_client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"OpenAI client initialization failed. Please ensure openai==1.54.0 and httpx==0.27.0 are installed: {e}")

        self.tools_cache: Optional[List[Dict[str, Any]]] = None
        self.product_profile = "common"

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP server"""
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
        """Call a specific MCP tool"""
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
        """Build a description of available tools for the LLM"""
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

            description += f"**{name}**\n"
            description += f"Description: {desc}\n"
            description += "Parameters:\n"

            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '')
                is_required = param_name in required
                req_marker = " (required)" if is_required else " (optional)"

                # Handle enum types
                if 'enum' in param_info:
                    enum_values = ', '.join(param_info['enum'])
                    description += f"  - {param_name} ({param_type}){req_marker}: {param_desc}\n"
                    description += f"    Options: {enum_values}\n"
                else:
                    description += f"  - {param_name} ({param_type}){req_marker}: {param_desc}\n"

            description += "\n"

        return description

    def sanitize_html(self, html: str) -> str:
        """Remove leading indentation from each line so markdown doesn't treat it as a code block."""
        if not html:
            return html
        cleaned_lines = []
        for line in html.splitlines():
            if line.strip() == "":
                cleaned_lines.append("")
            else:
                cleaned_lines.append(line.lstrip())
        return "\n".join(cleaned_lines)

    async def process_query(self, user_query: str) -> str:
        """
        Process user query using LLM to decide which tool to call
        """
        llm_response = ""
        try:
            # Get available tools
            tools_description = self.build_tools_description()

            # Create system prompt
            system_prompt = f"""You are an intelligent CVE database assistant. Your job is to understand user queries about CVE vulnerabilities and decide which tool to call.

{tools_description}

When the user asks a question:
1. Analyze their intent
2. Decide which tool is most appropriate
3. Extract the necessary parameters from their query
4. Return a JSON response with the tool name and arguments

Your response must be ONLY valid JSON in this format:
{{
    "tool": "tool_name",
    "arguments": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "reasoning": "brief explanation of why you chose this tool"
}}

Examples:
- User: "Show me CVE-2021-44228" -> {{"tool": "get_cve_details", "arguments": {{"cve_id": "CVE-2021-44228", "output_format": "detailed"}}, "reasoning": "User requested a specific CVE by ID"}}
- User: "Find critical vulnerabilities" -> {{"tool": "search_cves_by_severity", "arguments": {{"severity": "CRITICAL", "limit": 10, "output_format": "list"}}, "reasoning": "User wants to search by severity level"}}
- User: "SQL injection CVEs" -> {{"tool": "search_cves_by_keyword", "arguments": {{"keyword": "SQL injection", "limit": 10, "output_format": "list"}}, "reasoning": "User is searching for a specific vulnerability type"}}
- User: "Latest vulnerabilities" -> {{"tool": "list_recent_cves", "arguments": {{"limit": 10, "output_format": "list"}}, "reasoning": "User wants recent CVEs"}}

Remember:
- Always include "output_format" parameter (options: detailed, summary, json, markdown, list)
- For single CVE lookups, use "detailed" or "summary" format
- For searches, use "list" format
- Extract CVE IDs in format CVE-YYYY-NNNNN
- Map user's severity terms (critical, high, severe, etc.) to: CRITICAL, HIGH, MEDIUM, LOW
- Default limit is 10 unless user specifies otherwise
"""

            # Call OpenAI to decide which tool to use
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # Parse LLM response
            llm_response = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {llm_response}")

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in llm_response:
                llm_response = llm_response.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response:
                llm_response = llm_response.split("```")[1].split("```")[0].strip()

            tool_decision = json.loads(llm_response)

            tool_name = tool_decision.get('tool')
            arguments = tool_decision.get('arguments', {})
            reasoning = tool_decision.get('reasoning', '')

            logger.info(f"Calling tool: {tool_name} with args: {arguments}")
            logger.info(f"Reasoning: {reasoning}")

            # Call the MCP tool
            result = self.call_mcp_tool(tool_name, arguments)

            # Format the response for the user
            if result.get('status') == 'success':
                tool_result = result.get('result', {})

                if tool_result.get('status') == 'success':
                    # Check if we have rendered output from Jinja templates
                    rendered = tool_result.get('rendered')
                    count = tool_result.get('count')

                    # Build response - use Jinja rendered template directly
                    response_text = f"**🤖 Query Analysis:** {reasoning}\n\n"

                    if count:
                        response_text += f"**✅ Found {count} CVE(s)**\n\n"

                    # Return the Jinja-rendered template as-is
                    if rendered:
                        # sanitize to avoid markdown code block rendering due to indentation
                        rendered = self.sanitize_html(rendered)
                        response_text += rendered
                    else:
                        # Fallback if no rendered template (e.g., for JSON format)
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

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"LLM response was: {llm_response}")
            return "**⚠️ Failed to understand the query.** Please try rephrasing or being more specific."
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"**❌ An error occurred:** {str(e)}"

    def check_connection(self) -> bool:
        """Check if MCP server is accessible"""
        try:
            response = requests.get(f"{self.mcp_server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def setup_agent(self) -> bool:
        """Compatibility helper for legacy code: just test connection and cache tools."""
        connected = self.check_connection()
        if connected:
            self.get_available_tools()
        return connected

    def list_tools(self) -> List[Dict[str, Any]]:
        """Compatibility alias used by CLI."""
        return self.get_available_tools()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], product_profile: Optional[str] = None) -> Dict[str, Any]:
        """Compatibility wrapper to call MCP tool synchronously."""
        if product_profile:
            self.product_profile = product_profile
        return self.call_mcp_tool(tool_name, arguments)

    def disconnect(self):
        """Placeholder for compatibility (no long-lived connection to close)."""
        pass

