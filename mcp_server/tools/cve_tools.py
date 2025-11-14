"""
CVE Tools for MCP Server
"""
import logging
import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path to import mongo_service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mongo_service.repository_manager import get_repository_manager
from mongo_service.models import CVESearchFilter
from mcp_server.models import ProductProfile
from mcp_server.tools import mcp
from mcp_server.renderer import CVETemplateRenderer

logger = logging.getLogger(__name__)

# Get repository manager
repo_manager = get_repository_manager()

# Get template renderer
renderer = CVETemplateRenderer()


@mcp.tool(
    description="Fetch detailed information about a specific CVE by its CVE number (e.g., CVE-2021-44228)",
    input_schema={
        "type": "object",
        "properties": {
            "cve_id": {
                "type": "string",
                "description": "CVE identifier (e.g., CVE-2021-44228)"
            },
            "output_format": {
                "type": "string",
                "enum": ["detailed", "summary", "json", "markdown"],
                "default": "detailed",
                "description": "Output format"
            }
        },
        "required": ["cve_id"]
    },
    product_profiles=[ProductProfile.COMMON, ProductProfile.PREMIUM, ProductProfile.ADMIN],
    metadata={"category": "cve_lookup"}
)
def get_cve_details(cve_id: str, output_format: str = "detailed") -> Dict[str, Any]:
    """Fetch details of a CVE by ID."""
    logger.info(f"Fetching CVE details for: {cve_id}, format: {output_format}")

    cve_data = repo_manager.cve_details_repo.find_by_cve_number(cve_id)

    if cve_data:
        logger.info(f"Successfully fetched CVE details for: {cve_id}")

        # Render based on format
        if output_format == "json":
            rendered = renderer.render_cve_json(cve_data)
        elif output_format == "markdown":
            rendered = renderer.render_cve_markdown(cve_data)
        elif output_format == "summary":
            rendered = renderer.render_cve_summary(cve_data)
        else:  # detailed
            rendered = renderer.render_cve_detailed(cve_data)

        return {
            "status": "success",
            "data": cve_data,
            "rendered": rendered,
            "format": output_format
        }
    else:
        logger.warning(f"CVE not found: {cve_id}")
        return {"status": "error", "message": f"CVE {cve_id} not found"}


@mcp.tool(
    description="Search CVEs by severity level (CRITICAL, HIGH, MEDIUM, LOW)",
    input_schema={
        "type": "object",
        "properties": {
            "severity": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                "description": "Severity level"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum number of results"
            },
            "output_format": {
                "type": "string",
                "enum": ["list", "json"],
                "default": "list",
                "description": "Output format"
            }
        },
        "required": ["severity"]
    },
    product_profiles=[ProductProfile.COMMON, ProductProfile.PREMIUM, ProductProfile.ADMIN],
    metadata={"category": "cve_search"}
)
def search_cves_by_severity(severity: str, limit: int = 10, output_format: str = "list") -> Dict[str, Any]:
    """Search CVEs by severity level."""
    logger.info(f"Searching CVEs by severity: {severity}, limit: {limit}")

    cves = repo_manager.cve_details_repo.find_by_severity(severity, limit)

    # Render based on format
    if output_format == "list" and cves:
        rendered = renderer.render_cve_list(cves)
    else:
        rendered = None

    return {
        "status": "success",
        "count": len(cves),
        "data": cves,
        "rendered": rendered,
        "format": output_format
    }


@mcp.tool(
    description="Search CVEs by exploit code maturity level (Functional, Proof of Concept, Unproven, High)",
    input_schema={
        "type": "object",
        "properties": {
            "maturity": {
                "type": "string",
                "enum": ["Functional", "Proof of Concept", "Unproven", "High"],
                "description": "Exploit maturity level"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum number of results"
            },
            "output_format": {
                "type": "string",
                "enum": ["list", "json"],
                "default": "list",
                "description": "Output format"
            }
        },
        "required": ["maturity"]
    },
    product_profiles=[ProductProfile.COMMON, ProductProfile.PREMIUM, ProductProfile.ADMIN],
    metadata={"category": "cve_search"}
)
def search_cves_by_exploit_maturity(maturity: str, limit: int = 10, output_format: str = "list") -> Dict[str, Any]:
    """Search CVEs by exploit maturity."""
    logger.info(f"Searching CVEs by exploit maturity: {maturity}, limit: {limit}")

    cves = repo_manager.cve_details_repo.find_by_exploit_maturity(maturity, limit)

    # Render based on format
    if output_format == "list" and cves:
        rendered = renderer.render_cve_list(cves)
    else:
        rendered = None

    return {
        "status": "success",
        "count": len(cves),
        "data": cves,
        "rendered": rendered,
        "format": output_format
    }


@mcp.tool(
    description="Search CVEs by keyword in title or description",
    input_schema={
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Search keyword"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum number of results"
            },
            "output_format": {
                "type": "string",
                "enum": ["list", "json"],
                "default": "list",
                "description": "Output format"
            }
        },
        "required": ["keyword"]
    },
    product_profiles=[ProductProfile.COMMON, ProductProfile.PREMIUM, ProductProfile.ADMIN],
    metadata={"category": "cve_search"}
)
def search_cves_by_keyword(keyword: str, limit: int = 10, output_format: str = "list") -> Dict[str, Any]:
    """Search CVEs by keyword."""
    logger.info(f"Searching CVEs by keyword: {keyword}, limit: {limit}")

    cves = repo_manager.cve_details_repo.find_by_keyword(keyword, limit)

    # Render based on format
    if output_format == "list" and cves:
        rendered = renderer.render_cve_list(cves)
    else:
        rendered = None

    return {
        "status": "success",
        "count": len(cves),
        "data": cves,
        "rendered": rendered,
        "format": output_format
    }


@mcp.tool(
    description="Get most recent CVEs from the database",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum number of results"
            },
            "output_format": {
                "type": "string",
                "enum": ["list", "json"],
                "default": "list",
                "description": "Output format"
            }
        }
    },
    product_profiles=[ProductProfile.COMMON, ProductProfile.PREMIUM, ProductProfile.ADMIN],
    metadata={"category": "cve_list"}
)
def list_recent_cves(limit: int = 10, output_format: str = "list") -> Dict[str, Any]:
    """List most recent CVEs."""
    logger.info(f"Listing recent CVEs, limit: {limit}")

    cves = repo_manager.cve_details_repo.find_recent(limit)

    # Render based on format
    if output_format == "list" and cves:
        rendered = renderer.render_cve_list(cves)
    else:
        rendered = None

    return {
        "status": "success",
        "count": len(cves),
        "data": cves,
        "rendered": rendered,
        "format": output_format
    }


@mcp.tool(
    description="Search CVEs by CVSS score range",
    input_schema={
        "type": "object",
        "properties": {
            "min_score": {
                "type": "number",
                "description": "Minimum CVSS score",
                "minimum": 0,
                "maximum": 10
            },
            "max_score": {
                "type": "number",
                "description": "Maximum CVSS score",
                "minimum": 0,
                "maximum": 10
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum number of results"
            },
            "output_format": {
                "type": "string",
                "enum": ["list", "json"],
                "default": "list",
                "description": "Output format"
            }
        },
        "required": ["min_score", "max_score"]
    },
    product_profiles=[ProductProfile.PREMIUM, ProductProfile.ADMIN],
    metadata={"category": "cve_search"}
)
def search_cves_by_cvss_score(min_score: float, max_score: float, limit: int = 10, output_format: str = "list") -> Dict[str, Any]:
    """Search CVEs by CVSS score range."""
    logger.info(f"Searching CVEs by CVSS range: {min_score} - {max_score}, limit: {limit}")

    cves = repo_manager.cve_details_repo.find_by_cvss_range(min_score, max_score, limit)

    # Render based on format
    if output_format == "list" and cves:
        rendered = renderer.render_cve_list(cves)
    else:
        rendered = None

    return {
        "status": "success",
        "count": len(cves),
        "data": cves,
        "rendered": rendered,
        "format": output_format
    }


logger.info("CVE tools registered")
