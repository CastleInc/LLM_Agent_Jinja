"""
MongoDB Connection Manager
"""
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from mongo_service.config import mongo_config

logger = logging.getLogger(__name__)


class MongoConnection:
    """MongoDB connection manager with singleton pattern"""

    _instance: Optional['MongoConnection'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoConnection, cls).__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        """Establish MongoDB connection"""
        if self._client is not None:
            logger.info("MongoDB connection already exists")
            return True

        try:
            self._client = MongoClient(
                mongo_config.uri,
                maxPoolSize=mongo_config.max_pool_size,
                minPoolSize=mongo_config.min_pool_size,
                serverSelectionTimeoutMS=mongo_config.timeout,
            )

            # Test connection
            self._client.admin.command('ping')
            self._database = self._client[mongo_config.database]

            logger.info(f"Connected to MongoDB: {mongo_config.database}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._database = None
            return False

    def disconnect(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

    def get_database(self) -> Optional[Database]:
        """Get database instance"""
        if self._database is None:
            self.connect()
        return self._database

    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """Get collection instance"""
        db = self.get_database()
        if db is not None:
            return db[collection_name]
        return None

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._client is not None and self._database is not None


# Global connection instance
_mongo_connection = MongoConnection()


def get_mongo_connection() -> MongoConnection:
    """Get global MongoDB connection instance"""
    return _mongo_connection

