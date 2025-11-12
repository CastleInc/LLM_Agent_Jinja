"""
MongoDB connector for CVE data
"""
import os
from typing import List, Dict, Optional
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class CVEDatabase:
    """MongoDB CVE data handler"""

    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('MONGO_DB', 'cve_database')
        self.collection_name = os.getenv('MONGO_COLLECTION', 'cves')
        self.client = None
        self.db = None
        self.collection = None

    def connect(self) -> bool:
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.client.server_info()
            print(f"Connected to MongoDB: {self.db_name}.{self.collection_name}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_cve_by_id(self, cve_id: str) -> Optional[Dict]:
        try:
            return self.collection.find_one({'cveId': cve_id})
        except Exception as e:
            print(f"Error: {e}")
            return None

    def search_cves(self, query: Dict, limit: int = 10) -> List[Dict]:
        try:
            return list(self.collection.find(query).limit(limit))
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_cves_by_severity(self, severity: str, limit: int = 10) -> List[Dict]:
        query = {
            '$or': [
                {'metrics.cvssMetricV2.baseSeverity': severity.upper()},
                {'metrics.cvssMetricV31.cvssData.baseSeverity': severity.upper()}
            ]
        }
        return self.search_cves(query, limit)

    def get_cves_by_score_range(self, min_score: float, max_score: float, limit: int = 10) -> List[Dict]:
        query = {
            '$or': [
                {'metrics.cvssMetricV2.cvssData.baseScore': {'$gte': min_score, '$lte': max_score}},
                {'metrics.cvssMetricV31.cvssData.baseScore': {'$gte': min_score, '$lte': max_score}}
            ]
        }
        return self.search_cves(query, limit)

    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        query = {'descriptions.value': {'$regex': keyword, '$options': 'i'}}
        return self.search_cves(query, limit)
