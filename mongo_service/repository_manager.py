"""
Repository Manager - Central access point for all repositories
"""
import logging
from typing import Optional
from mongo_service.connection import get_mongo_connection
from mongo_service.repositories import CVERepository

logger = logging.getLogger(__name__)


class MongoRepositoryManager:
    """Central manager for all MongoDB repositories"""

    _instance: Optional['MongoRepositoryManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoRepositoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connection = get_mongo_connection()
        self._cve_details_repo: Optional[CVERepository] = None
        self._initialized = True

        # Ensure connection is established
        if not self._connection.is_connected:
            self._connection.connect()

    @property
    def cve_details_repo(self) -> CVERepository:
        """Get CVE details repository"""
        if self._cve_details_repo is None:
            self._cve_details_repo = CVERepository()
        return self._cve_details_repo

    def disconnect(self):
        """Disconnect all repositories"""
        self._connection.disconnect()
        logger.info("Repository manager disconnected")


# Global repository manager instance
_repository_manager: Optional[MongoRepositoryManager] = None


def get_repository_manager() -> MongoRepositoryManager:
    """Get global repository manager instance"""
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = MongoRepositoryManager()
    return _repository_manager

