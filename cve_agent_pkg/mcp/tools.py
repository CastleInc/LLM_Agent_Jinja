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
                "description": "Get detailed CVE information by ID with formatted output",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "cve_id": {"type": "string", "description": "CVE ID (e.g., CVE-1999-0095)"},
                        "format": {
                            "type": "string",
                            "enum": ["detailed", "summary", "json", "markdown"],
                            "default": "detailed"
                        }
                    },
                    "required": ["cve_id"]
                }
            },
            {
                "name": "search_cves_by_severity",
                "description": "Search CVEs by severity level",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                        },
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                    "required": ["severity"]
                }
            },
            {
                "name": "search_cves_by_score",
                "description": "Search CVEs by CVSS score range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "min_score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
                        "max_score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["min_score", "max_score"]
                }
            },
            {
                "name": "search_cves_by_keyword",
                "description": "Search CVEs by keyword in descriptions",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["keyword"]
                }
            },
            {
                "name": "get_cve_statistics",
                "description": "Get CVE database statistics",
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
                "search_cves_by_severity": self._search_cves_by_severity,
                "search_cves_by_score": self._search_cves_by_score,
                "search_cves_by_keyword": self._search_cves_by_keyword,
                "get_cve_statistics": self._get_cve_statistics
            }

            if tool_name not in tool_map:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

            return tool_map[tool_name](**arguments)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_cve_details(self, cve_id: str, format: str = "detailed") -> Dict[str, Any]:
        cve = self.db.get_cve_by_id(cve_id)
        if not cve:
            return {"success": False, "error": f"CVE {cve_id} not found"}

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
            "data": {"cve_id": cve_id, "format": format, "rendered_output": rendered, "raw_data": cve}
        }

    def _search_cves_by_severity(self, severity: str, limit: int = 10) -> Dict[str, Any]:
        cves = self.db.get_cves_by_severity(severity, limit)
        if not cves:
            return {"success": False, "error": f"No CVEs found with severity {severity}"}

        for cve in cves:
            if '_id' in cve:
                del cve['_id']

        return {
            "success": True,
            "data": {
                "severity": severity,
                "count": len(cves),
                "rendered_output": self.renderer.render_list(cves),
                "cves": cves
            }
        }

    def _search_cves_by_score(self, min_score: float, max_score: float, limit: int = 10) -> Dict[str, Any]:
        cves = self.db.get_cves_by_score_range(min_score, max_score, limit)
        if not cves:
            return {"success": False, "error": f"No CVEs found between {min_score} and {max_score}"}

        for cve in cves:
            if '_id' in cve:
                del cve['_id']

        return {
            "success": True,
            "data": {
                "min_score": min_score,
                "max_score": max_score,
                "count": len(cves),
                "rendered_output": self.renderer.render_list(cves),
                "cves": cves
            }
        }

    def _search_cves_by_keyword(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        cves = self.db.search_by_keyword(keyword, limit)
        if not cves:
            return {"success": False, "error": f"No CVEs found matching '{keyword}'"}

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

    def _get_cve_statistics(self) -> Dict[str, Any]:
        try:
            stats = {
                "total_cves": self.db.collection.count_documents({}),
                "by_severity": {
                    severity: len(self.db.get_cves_by_severity(severity, limit=1000))
                    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                }
            }
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}
