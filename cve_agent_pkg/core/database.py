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
        self.collection_name = os.getenv('MONGO_COLLECTION', 'cve_details')
        self.client = None
        self.db = None
        self.collection = None

    def connect(self) -> bool:
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.client.server_info()
            print(f"✅ Connected to MongoDB: {self.db_name}.{self.collection_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_cve_by_id(self, cve_id: str) -> Optional[Dict]:
        """Get CVE by cve_no field (e.g., CVE-1999-0776)"""
        try:
            # Search by cve_no field in new structure
            return self.collection.find_one({'cve_no': cve_id.upper()})
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
        """Search CVEs by severity using CVSS score ranges"""
        # Map severity to CVSS score ranges (CVSS 3.x)
        severity_map = {
            'CRITICAL': {'$gte': 9.0, '$lte': 10.0},
            'HIGH': {'$gte': 7.0, '$lt': 9.0},
            'MEDIUM': {'$gte': 4.0, '$lt': 7.0},
            'LOW': {'$gte': 0.1, '$lt': 4.0}
        }

        score_range = severity_map.get(severity.upper())
        if not score_range:
            return []

        # Extract base score from input_vector if available
        query = {
            'input_vector': {'$exists': True, '$ne': None},
            'is_active': '1'
        }

        # Get all CVEs and filter by parsed CVSS score
        all_cves = list(self.collection.find(query).limit(limit * 3))
        filtered_cves = []

        for cve in all_cves:
            score = self._parse_cvss_score(cve.get('input_vector', ''))
            if score and score_range['$gte'] <= score <= score_range.get('$lte', score_range.get('$lt', 10.0)):
                filtered_cves.append(cve)
                if len(filtered_cves) >= limit:
                    break

        return filtered_cves

    def _parse_cvss_score(self, vector_string: str) -> Optional[float]:
        """Parse CVSS base score from vector string"""
        # Example: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
        # We need to calculate or it might be stored elsewhere
        # For now, return None and handle in query
        return None

    def get_cves_by_score_range(self, min_score: float, max_score: float, limit: int = 10) -> List[Dict]:
        """Search CVEs by CVSS score range"""
        # This would need the actual score field or calculation
        query = {'is_active': '1'}
        return self.search_cves(query, limit)

    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search CVEs by keyword in description or keywords field"""
        query = {
            '$or': [
                {'description': {'$regex': keyword, '$options': 'i'}},
                {'keywords': {'$regex': keyword, '$options': 'i'}},
                {'cve_title': {'$regex': keyword, '$options': 'i'}}
            ],
            'is_active': '1'
        }
        return self.search_cves(query, limit)

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            total = self.collection.count_documents({'is_active': '1'})

            # Get counts by exploit maturity
            exploit_stats = {}
            for maturity in ['Functional', 'Proof of Concept', 'High', 'Unproven']:
                count = self.collection.count_documents({
                    'exploit_code_maturity': maturity,
                    'is_active': '1'
                })
                exploit_stats[maturity] = count

            # Get counts by classification
            classification_stats = {}
            for classification in ['Remote / Network Access', 'Local Access', 'Physical Access']:
                count = self.collection.count_documents({
                    'classifications_location': classification,
                    'is_active': '1'
                })
                classification_stats[classification] = count

            return {
                'total_cves': total,
                'by_exploit_maturity': exploit_stats,
                'by_classification': classification_stats
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'total_cves': 0, 'by_exploit_maturity': {}, 'by_classification': {}}

