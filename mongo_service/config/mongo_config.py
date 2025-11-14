"""
MongoDB Configuration Module
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class MongoConfig:
    """MongoDB configuration settings"""

    def __init__(self):
        self.uri: str = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.database: str = os.getenv('MONGO_DB', 'genai_kb')
        self.collection: str = os.getenv('MONGO_COLLECTION', 'cve_details')
        self.pool_size: int = int(os.getenv('MONGO_POOL_SIZE', '10'))
        self.timeout: int = int(os.getenv('MONGO_TIMEOUT', '5000'))
        self.max_pool_size: int = int(os.getenv('MONGO_MAX_POOL_SIZE', '50'))
        self.min_pool_size: int = int(os.getenv('MONGO_MIN_POOL_SIZE', '10'))

    def get_connection_string(self) -> str:
        """Get MongoDB connection string"""
        return self.uri

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'uri': self.uri,
            'database': self.database,
            'collection': self.collection,
            'pool_size': self.pool_size,
            'timeout': self.timeout,
            'max_pool_size': self.max_pool_size,
            'min_pool_size': self.min_pool_size,
        }


# Global config instance
mongo_config = MongoConfig()

