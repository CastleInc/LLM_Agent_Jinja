import logging
import os
from typing import Any, Dict

from cstgenai.common_entities.model.product_profile import ProductProfile
from cstgenai.common_services.config.mongo_repository_manager import (
    MongoRepositoryManager,
)
from pymongo.database import Database

from cstgenai.common_services.db.connection import get_repository_manager
from mcp_server.tools.main import mcp

logger: logging.Logger = logging.getLogger(__name__)

db: MongoRepositoryManager = get_repository_manager()


@mcp.tool(cve={"product_profiles": [ProductProfile.COPY()]})
def fetch_cve_details(cve_id: str) -> Dict[str, Any]:
    """Fetch details of a CVE ID."""
    logger.info(f"Fetching CVE details (cve_id)")
    cve_db = db.cve_details_repo.find_one(
        {"cve_id": cve_id}, projection={"_id": 0}
    )

    if cve_db:
        return {"data": cve_db}
    else:
        logger.error(f"CVE not found ({cve_id})")
        return {"error": "CVE not found"}


def cve_dict(cve_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return cve_dict without the cve key if present."""
    if "cve" in cve_dict:
        del cve_dict["cve"]
    return cve_dict


@mcp.tool(cve={"product_profiles": [ProductProfile.COPY()]})
def fetch_cve_details_filtered(cve_id: str) -> Dict[str, Any]:
    """Fetch details of a CVE ID."""
    logger.info(f"Successfully fetched CVE details for ID: {cve_id}")
    cve_dict = fetch_cve_details(cve_id)
    if "error" in cve_dict:
        return cve_dict

    return {"data": cve_dict["data"]}