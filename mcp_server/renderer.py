"""
Template rendering module for CVE data
"""
import os
import json
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape


class CVETemplateRenderer:
    """Jinja2 template renderer for CVE data"""

    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render_cve_detailed(self, cve_data: Dict[str, Any]) -> str:
        """Render detailed CVE view"""
        template = self.env.get_template('cve_detailed.jinja')
        return template.render(cve=cve_data)

    def render_cve_summary(self, cve_data: Dict[str, Any]) -> str:
        """Render summary CVE view"""
        template = self.env.get_template('cve_summary.jinja')
        return template.render(cve=cve_data)

    def render_cve_list(self, cves: List[Dict[str, Any]]) -> str:
        """Render list of CVEs"""
        template = self.env.get_template('cve_list.jinja')
        return template.render(cves=cves)

    def render_cve_markdown(self, cve_data: Dict[str, Any]) -> str:
        """Render CVE in markdown format"""
        template = self.env.get_template('cve_markdown.jinja')
        return template.render(cve=cve_data)

    def render_cve_json(self, cve_data: Dict[str, Any]) -> str:
        """Render CVE as formatted JSON"""
        return json.dumps(cve_data, indent=2, default=str)
