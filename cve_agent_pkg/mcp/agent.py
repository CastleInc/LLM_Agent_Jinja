"""
MCP Agent - Routes queries to appropriate tools
"""
from typing import Dict, List, Any
import json
import re
import os
from dotenv import load_dotenv
from cve_agent_pkg.mcp.tools import CVEMCPTools

load_dotenv()


class MCPAgent:
    """Agent for processing natural language CVE queries"""

    def __init__(self):
        self.tools = CVEMCPTools()
        self.conversation_history = []
        self.llm_model_name = os.getenv('LLM_MODEL_NAME', 'gpt-4')
        self.llm_model_url = os.getenv('LLM_MODEL_URL', 'https://api.openai.com/v1')

    def connect(self) -> bool:
        return self.tools.connect()

    def disconnect(self):
        self.tools.disconnect()

    def process_query(self, user_query: str, llm_client=None) -> Dict[str, Any]:
        """Process query with LLM or rule-based fallback"""
        self.conversation_history.append({"role": "user", "content": user_query})

        if llm_client:
            return self._process_with_llm(user_query, llm_client)
        return self._process_rule_based(user_query)

    def _process_with_llm(self, user_query: str, llm_client) -> Dict[str, Any]:
        """Process using LLM with tool calling"""
        try:
            # Use LLM model from environment
            response = llm_client.chat.completions.create(
                model=self.llm_model_name,
                messages=[
                    {"role": "system", "content": "You are a CVE security assistant. Use tools to answer CVE queries."},
                    *self.conversation_history
                ],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"]
                    }
                } for t in self.tools.get_tool_definitions()],
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                result = self.tools.execute_tool(tool_name, tool_args)

                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls
                })

                return {
                    "success": result["success"],
                    "query": user_query,
                    "tool_called": tool_name,
                    "tool_arguments": tool_args,
                    "result": result,
                    "rendered_output": result.get("data", {}).get("rendered_output", ""),
                    "llm_used": True,
                    "llm_model": self.llm_model_name
                }

            return {
                "success": True,
                "query": user_query,
                "response": message.content,
                "llm_used": True,
                "llm_model": self.llm_model_name
            }
        except Exception as e:
            return {"success": False, "error": str(e), "query": user_query}

    def _process_rule_based(self, user_query: str) -> Dict[str, Any]:
        """Rule-based processing without LLM"""
        query_lower = user_query.lower()

        # Check for CVE ID (CVE-YYYY-NNNNN format)
        cve_match = re.search(r'cve-\d{4}-\d{4,}', query_lower)
        if cve_match:
            cve_id = cve_match.group(0).upper()
            format_type = "summary" if "summary" in query_lower else "detailed"
            result = self.tools.execute_tool("get_cve_details", {"cve_id": cve_id, "format": format_type})

            return {
                "success": result["success"],
                "query": user_query,
                "tool_called": "get_cve_details",
                "tool_arguments": {"cve_id": cve_id, "format": format_type},
                "result": result,
                "rendered_output": result.get("data", {}).get("rendered_output", ""),
                "llm_used": False
            }

        # Check for severity/exploit maturity keywords
        maturity_map = {
            "functional": "Functional",
            "proof of concept": "Proof of Concept",
            "high": "High",
            "unproven": "Unproven"
        }

        for keyword, maturity in maturity_map.items():
            if keyword in query_lower:
                result = self.tools.execute_tool("search_cves_by_exploit_maturity", {"maturity": maturity, "limit": 5})
                return {
                    "success": result["success"],
                    "query": user_query,
                    "tool_called": "search_cves_by_exploit_maturity",
                    "tool_arguments": {"maturity": maturity, "limit": 5},
                    "result": result,
                    "rendered_output": result.get("data", {}).get("rendered_output", ""),
                    "llm_used": False
                }

        # Keyword search in descriptions, titles, and keywords
        if any(word in query_lower for word in ["search", "find", "look"]):
            keywords = query_lower.replace("search for", "").replace("find", "").replace("look for", "").strip()
            if keywords:
                result = self.tools.execute_tool("search_cves_by_keyword", {"keyword": keywords, "limit": 5})
                return {
                    "success": result["success"],
                    "query": user_query,
                    "tool_called": "search_cves_by_keyword",
                    "tool_arguments": {"keyword": keywords, "limit": 5},
                    "result": result,
                    "rendered_output": result.get("data", {}).get("rendered_output", ""),
                    "llm_used": False
                }

        # Help message
        return {
            "success": True,
            "query": user_query,
            "response": "Try: 'Show me CVE-XXXX-XXXX', 'Find functional exploits', or 'Search for SQL injection'",
            "llm_used": False
        }

    def get_available_tools(self) -> List[Dict[str, Any]]:
        return self.tools.get_tool_definitions()
