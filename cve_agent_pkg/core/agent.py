"""
Legacy CVE Agent (use MCPAgent instead)
"""
from typing import Dict, List
from cve_agent_pkg.core.database import CVEDatabase
from cve_agent_pkg.core.renderer import CVETemplateRenderer


class CVEAgent:
    """Legacy agent - use MCPAgent for new implementations"""

    def __init__(self):
        self.db = CVEDatabase()
        self.renderer = CVETemplateRenderer()
        self.connected = False
        self.functions = self._get_function_definitions()

    def connect(self) -> bool:
        self.connected = self.db.connect()
        return self.connected

    def disconnect(self):
        self.db.disconnect()
        self.connected = False

    def _get_function_definitions(self) -> List[Dict]:
        return [
            {
                "name": "get_cve_details",
                "description": "Get CVE details by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cve_id": {"type": "string"},
                        "format": {"type": "string", "enum": ["detailed", "summary", "json", "markdown"]}
                    },
                    "required": ["cve_id"]
                }
            },
            {
                "name": "search_cves_by_severity",
                "description": "Search CVEs by severity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["severity"]
                }
            }
        ]

    def get_function_definitions(self) -> List[Dict]:
        return self.functions

    def get_cve_details(self, cve_id: str, format: str = "detailed") -> str:
        cve = self.db.get_cve_by_id(cve_id)
        if not cve:
            return f"CVE {cve_id} not found"

        if '_id' in cve:
            del cve['_id']

        renderer_map = {
            "detailed": self.renderer.render_detailed,
            "summary": self.renderer.render_summary,
            "json": self.renderer.render_json,
            "markdown": self.renderer.render_markdown
        }
        return renderer_map.get(format, self.renderer.render_detailed)(cve)

    def search_cves_by_severity(self, severity: str, limit: int = 10) -> str:
        cves = self.db.get_cves_by_severity(severity, limit)
        if not cves:
            return f"No CVEs found with severity {severity}"

        for cve in cves:
            if '_id' in cve:
                del cve['_id']

        return self.renderer.render_list(cves)

    def search_cves_by_score(self, min_score: float, max_score: float, limit: int = 10) -> str:
        cves = self.db.get_cves_by_score_range(min_score, max_score, limit)
        if not cves:
            return f"No CVEs found with score between {min_score} and {max_score}"

        for cve in cves:
            if '_id' in cve:
                del cve['_id']

        return self.renderer.render_list(cves)

    def search_cves_by_keyword(self, keyword: str, limit: int = 10) -> str:
        cves = self.db.search_by_keyword(keyword, limit)
        if not cves:
            return f"No CVEs found matching keyword '{keyword}'"

        for cve in cves:
            if '_id' in cve:
                del cve['_id']

        return self.renderer.render_list(cves)

    def execute_function(self, function_name: str, arguments: Dict) -> str:
        function_map = {
            "get_cve_details": self.get_cve_details,
            "search_cves_by_severity": self.search_cves_by_severity,
            "search_cves_by_score": self.search_cves_by_score,
            "search_cves_by_keyword": self.search_cves_by_keyword
        }

        if function_name not in function_map:
            return f"Unknown function: {function_name}"

        try:
            return function_map[function_name](**arguments)
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
