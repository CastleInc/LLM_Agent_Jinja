"""
MCP Tools for CVE Agent
"""
from typing import Dict, List, Any
from cve_agent_pkg.core.database import CVEDatabase
from cve_agent_pkg.core.renderer import CVETemplateRenderer


class CVEMCPTools:
    """MCP Tools for CVE data retrieval"""

    def __init__(self):
        self.db = CVEDatabase()
        self.renderer = CVETemplateRenderer()
        self.connected = False

    def connect(self) -> bool:
        self.connected = self.db.connect()
        return self.connected

    def disconnect(self):
        self.db.disconnect()
        self.connected = False

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get MCP tool definitions for LLM"""
        return [
            {
                "name": "get_cve_details",
                "description": "Get detailed CVE information by CVE number (e.g., CVE-1999-0776). Returns vulnerability title, description, exploit code maturity (Functional/Proof of Concept/Unproven), CVSS vector, classifications (location, attack type, impact), solution, and additional technical details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "cve_id": {"type": "string", "description": "CVE number (e.g., CVE-1999-0776)"},
                        "format": {
                            "type": "string",
                            "enum": ["detailed", "summary", "json", "markdown"],
                            "default": "detailed",
                            "description": "Output format: detailed (full HTML), summary (condensed), json (raw data), markdown (markdown format)"
                        }
                    },
                    "required": ["cve_id"]
                }
            },
            {
                "name": "search_cves_by_exploit_maturity",
                "description": "Search CVEs by exploit code maturity level. Returns CVEs with matching exploit status including title, description, keywords, and classification details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "maturity": {
                            "type": "string",
                            "enum": ["Functional", "Proof of Concept", "High", "Unproven"],
                            "description": "Exploit maturity: Functional (working exploit exists), Proof of Concept (demo code exists), High (highly exploitable), Unproven (no known exploit)"
                        },
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                    "required": ["maturity"]
                }
            },
            {
                "name": "search_cves_by_classification",
                "description": "Search CVEs by classification type (location, attack type, or impact). Returns vulnerabilities matching the specified classification with full details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "classification_type": {
                            "type": "string",
                            "enum": ["location", "attack_type", "impact"],
                            "description": "Type of classification to search"
                        },
                        "classification_value": {
                            "type": "string",
                            "description": "Classification value (e.g., 'Remote / Network Access', 'Input Manipulation', 'Loss of Confidentiality')"
                        },
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["classification_type", "classification_value"]
                }
            },
            {
                "name": "search_cves_by_keyword",
                "description": "Search CVEs by keyword in description, title, or keywords field. Returns matching vulnerabilities with their exploit maturity, classifications, and details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "Keyword to search (e.g., 'traversal', 'SQL injection', 'buffer overflow')"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["keyword"]
                }
            },
            {
                "name": "search_cves_by_cisa_kev",
                "description": "Search CVEs that are in CISA's Known Exploited Vulnerabilities (KEV) catalog. Returns actively exploited vulnerabilities requiring immediate attention.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10}
                    }
                }
            },
            {
                "name": "get_cve_statistics",
                "description": "Get comprehensive CVE database statistics including total count, distribution by exploit maturity, classification types, and CISA KEV status.",
                "input_schema": {"type": "object", "properties": {}}
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool"""
        if not self.connected:
            return {"success": False, "error": "Not connected to database"}

        try:
            tool_map = {
                "get_cve_details": self._get_cve_details,
                "search_cves_by_exploit_maturity": self._search_cves_by_exploit_maturity,
                "search_cves_by_classification": self._search_cves_by_classification,
                "search_cves_by_keyword": self._search_cves_by_keyword,
                "search_cves_by_cisa_kev": self._search_cves_by_cisa_kev,
                "get_cve_statistics": self._get_cve_statistics
            }

            if tool_name not in tool_map:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

            return tool_map[tool_name](**arguments)
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

    def _get_cve_details(self, cve_id: str, format: str = "detailed") -> Dict[str, Any]:
        """Get CVE details by cve_no"""
        cve = self.db.get_cve_by_id(cve_id)

        if not cve:
            return {
                "success": False,
                "error": f"CVE {cve_id} not found in database",
                "message": f"The requested CVE '{cve_id}' does not exist in the database or may be inactive. Please verify the CVE number and try again."
            }

        if '_id' in cve:
            del cve['_id']

        renderer_map = {
            "detailed": self.renderer.render_detailed,
            "summary": self.renderer.render_summary,
            "json": self.renderer.render_json,
            "markdown": self.renderer.render_markdown
        }

        rendered = renderer_map.get(format, self.renderer.render_detailed)(cve)

        return {
            "success": True,
            "data": {
                "cve_id": cve_id,
                "cve_title": cve.get("cve_title", "N/A"),
                "exploit_maturity": cve.get("exploit_code_maturity", "N/A"),
                "format": format,
                "rendered_output": rendered,
                "raw_data": cve
            }
        }

    def _search_cves_by_exploit_maturity(self, maturity: str, limit: int = 10) -> Dict[str, Any]:
        """Search CVEs by exploit_code_maturity field"""
        try:
            query = {
                "exploit_code_maturity": maturity,
                "is_active": "1"
            }
            cves = self.db.search_cves(query, limit)

            if not cves:
                return {
                    "success": False,
                    "error": f"No CVEs found with exploit maturity '{maturity}'",
                    "message": f"No active CVEs with exploit code maturity level '{maturity}' were found in the database. Try a different maturity level (Functional, Proof of Concept, High, or Unproven)."
                }

            for cve in cves:
                if '_id' in cve:
                    del cve['_id']

            return {
                "success": True,
                "data": {
                    "exploit_maturity": maturity,
                    "count": len(cves),
                    "rendered_output": self.renderer.render_list(cves),
                    "cves": cves
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}

    def _search_cves_by_classification(self, classification_type: str, classification_value: str, limit: int = 10) -> Dict[str, Any]:
        """Search CVEs by classification fields"""
        try:
            field_map = {
                "location": "classifications_location",
                "attack_type": "classifications_attack_type",
                "impact": "classifications_impact"
            }

            field_name = field_map.get(classification_type)
            if not field_name:
                return {"success": False, "error": f"Invalid classification type: {classification_type}"}

            query = {
                field_name: classification_value,
                "is_active": "1"
            }
            cves = self.db.search_cves(query, limit)

            if not cves:
                return {
                    "success": False,
                    "error": f"No CVEs found with {classification_type} = '{classification_value}'",
                    "message": f"No active CVEs matching the classification '{classification_type}: {classification_value}' were found. Please verify the classification value and try again."
                }

            for cve in cves:
                if '_id' in cve:
                    del cve['_id']

            return {
                "success": True,
                "data": {
                    "classification_type": classification_type,
                    "classification_value": classification_value,
                    "count": len(cves),
                    "rendered_output": self.renderer.render_list(cves),
                    "cves": cves
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}

    def _search_cves_by_keyword(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        """Search CVEs by keyword in description, cve_title, or keywords fields"""
        cves = self.db.search_by_keyword(keyword, limit)

        if not cves:
            return {
                "success": False,
                "error": f"No CVEs found matching keyword '{keyword}'",
                "message": f"No active CVEs containing the keyword '{keyword}' were found in descriptions, titles, or keywords. Try a different search term or broader keyword."
            }

        for cve in cves:
            if '_id' in cve:
                del cve['_id']

        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "count": len(cves),
                "rendered_output": self.renderer.render_list(cves),
                "cves": cves
            }
        }

    def _search_cves_by_cisa_kev(self, limit: int = 10) -> Dict[str, Any]:
        """Search CVEs in CISA KEV catalog"""
        try:
            query = {
                "cisa_key": "Yes",
                "is_active": "1"
            }
            cves = self.db.search_cves(query, limit)

            if not cves:
                return {
                    "success": False,
                    "error": "No CVEs found in CISA KEV catalog",
                    "message": "No CVEs marked as CISA Known Exploited Vulnerabilities were found in the database."
                }

            for cve in cves:
                if '_id' in cve:
                    del cve['_id']

            return {
                "success": True,
                "data": {
                    "cisa_kev": True,
                    "count": len(cves),
                    "rendered_output": self.renderer.render_list(cves),
                    "cves": cves
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}

    def _get_cve_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = self.db.get_statistics()

            if stats.get('total_cves', 0) == 0:
                return {
                    "success": False,
                    "error": "No CVE data available",
                    "message": "The database appears to be empty or contains no active CVEs."
                }

            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "error": f"Failed to get statistics: {str(e)}"}
