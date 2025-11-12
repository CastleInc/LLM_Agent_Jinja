"""
Jinja2 template rendering for CVE data
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, List
import os


class CVETemplateRenderer:
    """Render CVE data using Jinja2 templates"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            package_dir = os.path.dirname(os.path.dirname(__file__))
            template_dir = os.path.join(package_dir, 'templates')

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.env.filters['severity_color'] = lambda s: {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(s.upper(), '⚪')
        self.env.filters['format_date'] = lambda d: d[:10] if d else 'N/A'

    def render_detailed(self, cve: Dict) -> str:
        return self.env.get_template('cve_detailed.jinja').render(cve=cve)

    def render_summary(self, cve: Dict) -> str:
        return self.env.get_template('cve_summary.jinja').render(cve=cve)

    def render_list(self, cves: List[Dict]) -> str:
        return self.env.get_template('cve_list.jinja').render(cves=cves)

    def render_json(self, cve: Dict) -> str:
        return self.env.get_template('cve_json.jinja').render(cve=cve)

    def render_markdown(self, cve: Dict) -> str:
        return self.env.get_template('cve_markdown.jinja').render(cve=cve)
