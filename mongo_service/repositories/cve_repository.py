"""
CVE Repository - Data access layer for CVE collection
Optimized for large collections (500k+ documents)
"""
import logging
from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from mongo_service.connection import get_mongo_connection
from mongo_service.config import mongo_config
from mongo_service.models import CVESearchFilter

logger = logging.getLogger(__name__)


class CVERepository:
    """Repository for CVE data operations - optimized for large datasets"""

    def __init__(self):
        self._connection = get_mongo_connection()
        self._collection: Optional[Collection] = None
        self._indexes_created = False

    def _get_collection(self) -> Optional[Collection]:
        """Get CVE collection and ensure indexes"""
        if self._collection is None:
            self._collection = self._connection.get_collection(mongo_config.collection)
            if self._collection is not None and not self._indexes_created:
                self._ensure_indexes()
        return self._collection

    def _ensure_indexes(self):
        """Create indexes for efficient queries on large collections"""
        try:
            collection = self._collection
            if collection is None:
                return

            # Check existing indexes
            existing_indexes = list(collection.list_indexes())
            existing_names = {idx['name'] for idx in existing_indexes}

            logger.info(f"Existing indexes: {existing_names}")

            # Define indexes for performance
            indexes_to_create = []

            # 1. CVE number - unique, most common query
            if 'cve_number_1' not in existing_names:
                indexes_to_create.append(IndexModel([("cve_number", ASCENDING)], name="cve_number_1", unique=True))

            # 2. Severity - frequently filtered
            if 'severity_1' not in existing_names:
                indexes_to_create.append(IndexModel([("severity", ASCENDING)], name="severity_1"))

            # 3. Exploit code maturity - frequently filtered
            if 'exploit_code_maturity_1' not in existing_names:
                indexes_to_create.append(IndexModel([("exploit_code_maturity", ASCENDING)], name="exploit_code_maturity_1"))

            # 4. CVSS score - for range queries
            if 'cvss_score_1' not in existing_names and 'cvss_score_-1' not in existing_names:
                # Prefer descending for typical use-case (top scores first)
                indexes_to_create.append(IndexModel([("cvss_score", DESCENDING)], name="cvss_score_1"))

            # 5. Compound index for severity + cvss
            if 'severity_1_cvss_score_-1' not in existing_names:
                indexes_to_create.append(
                    IndexModel([("severity", ASCENDING), ("cvss_score", DESCENDING)],
                              name="severity_1_cvss_score_-1")
                )

            # 6. Text index for keyword search; include both 'title' and 'cve_title'
            if 'text_search' not in existing_names:
                indexes_to_create.append(
                    IndexModel([("title", TEXT), ("cve_title", TEXT), ("description", TEXT), ("keywords", TEXT)],
                              name="text_search")
                )

            # Create indexes if needed
            if indexes_to_create:
                logger.info(f"Creating {len(indexes_to_create)} indexes for large collection optimization...")
                collection.create_indexes(indexes_to_create)
                logger.info("✓ Indexes created successfully")
            else:
                logger.info("✓ All indexes already exist")

            self._indexes_created = True

        except Exception as e:
            logger.warning(f"Could not create indexes (may not have permissions): {e}")
            # Continue anyway - queries will work, just slower
            self._indexes_created = True

    def find_one(self, query: Dict[str, Any], projection: Optional[Dict[str, int]] = None) -> Optional[Dict[str, Any]]:
        """Find one CVE document"""
        try:
            collection = self._get_collection()
            if collection is None:
                logger.error("Collection not available")
                return None

            result = collection.find_one(query, projection)
            if result:
                logger.debug(f"Found CVE: {query}")
            return result

        except Exception as e:
            logger.error(f"Error finding CVE: {e}")
            return None

    def find_by_cve_number(self, cve_number: str) -> Optional[Dict[str, Any]]:
        """Find CVE by CVE number - uses index for O(log n) performance"""
        return self.find_one({"cve_number": cve_number}, projection={"_id": 0})

    def find_many(self, query: Dict[str, Any], limit: int = 10, skip: int = 0,
                  projection: Optional[Dict[str, int]] = None, sort_field: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find multiple CVE documents - optimized with indexes and limits"""
        try:
            collection = self._get_collection()
            if collection is None:
                logger.error("Collection not available")
                return []

            # Use efficient cursor with limit to avoid loading all 500k docs
            cursor = collection.find(query, projection)

            # Add sorting if specified
            if sort_field:
                cursor = cursor.sort(sort_field, DESCENDING)

            # Always apply skip and limit for large collections
            cursor = cursor.skip(skip).limit(min(limit, 100))  # Cap at 100 for safety

            results = list(cursor)
            logger.debug(f"Found {len(results)} CVEs")
            return results

        except Exception as e:
            logger.error(f"Error finding CVEs: {e}")
            return []

    def find_by_severity(self, severity: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find CVEs by severity level - uses severity index"""
        query = {"severity": severity.upper()}
        return self.find_many(query, limit=limit, projection={"_id": 0}, sort_field="cvss_score")

    def find_by_exploit_maturity(self, maturity: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find CVEs by exploit maturity - uses index"""
        query = {"exploit_code_maturity": {"$regex": f"^{maturity}", "$options": "i"}}
        return self.find_many(query, limit=limit, projection={"_id": 0}, sort_field="cvss_score")

    def find_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find CVEs by keyword - uses text index for performance"""
        try:
            collection = self._get_collection()
            if collection is None:
                return []

            # Use text search index for better performance on large collections
            query = {"$text": {"$search": keyword}}
            projection = {"_id": 0, "score": {"$meta": "textScore"}}

            cursor = collection.find(query, projection).sort([("score", {"$meta": "textScore"})]).limit(min(limit, 100))
            results = list(cursor)

            # Remove the score field from results
            for result in results:
                result.pop('score', None)

            logger.debug(f"Text search found {len(results)} CVEs")
            return results

        except Exception as e:
            logger.warning(f"Text search failed, falling back to regex: {e}")
            # Fallback to regex if text index doesn't exist
            query = {
                "$or": [
                    {"title": {"$regex": keyword, "$options": "i"}},
                    {"cve_title": {"$regex": keyword, "$options": "i"}},
                    {"description": {"$regex": keyword, "$options": "i"}},
                    {"keywords": {"$regex": keyword, "$options": "i"}}
                ]
            }
            return self.find_many(query, limit=limit, projection={"_id": 0})

    def find_by_cvss_range(self, min_score: float, max_score: float, limit: int = 10) -> List[Dict[str, Any]]:
        """Find CVEs by CVSS score range - uses cvss_score index"""
        query = {
            "cvss_score": {
                "$gte": min_score,
                "$lte": max_score
            }
        }
        return self.find_many(query, limit=limit, projection={"_id": 0}, sort_field="cvss_score")

    def find_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find most recent CVEs - uses _id for efficiency on large collections"""
        try:
            collection = self._get_collection()
            if collection is None:
                return []

            # Use _id for sorting (natural order) - most efficient on large collections
            cursor = collection.find({}, {"_id": 0}).sort("_id", DESCENDING).limit(min(limit, 100))
            return list(cursor)

        except Exception as e:
            logger.error(f"Error finding recent CVEs: {e}")
            return []

    def search(self, search_filter: CVESearchFilter) -> List[Dict[str, Any]]:
        """Advanced search with multiple filters - optimized query building"""
        query: Dict[str, Any] = {}

        # Build compound query for indexed fields
        if search_filter.severity:
            query["severity"] = search_filter.severity.upper()

        if search_filter.exploit_maturity:
            query["exploit_code_maturity"] = {
                "$regex": f"^{search_filter.exploit_maturity}",
                "$options": "i"
            }

        if search_filter.min_cvss_score is not None or search_filter.max_cvss_score is not None:
            cvss_query: Dict[str, Any] = {}
            if search_filter.min_cvss_score is not None:
                cvss_query["$gte"] = search_filter.min_cvss_score
            if search_filter.max_cvss_score is not None:
                cvss_query["$lte"] = search_filter.max_cvss_score
            query["cvss_score"] = cvss_query

        # Handle keyword search separately for text index
        if search_filter.keyword:
            # Use text search if other filters are minimal
            if len(query) == 0:
                return self.find_by_keyword(search_filter.keyword, search_filter.limit)
            else:
                # Add keyword as $or condition
                query["$or"] = [
                    {"title": {"$regex": search_filter.keyword, "$options": "i"}},
                    {"cve_title": {"$regex": search_filter.keyword, "$options": "i"}},
                    {"description": {"$regex": search_filter.keyword, "$options": "i"}}
                ]

        return self.find_many(
            query,
            limit=search_filter.limit,
            skip=search_filter.skip,
            projection={"_id": 0},
            sort_field="cvss_score"
        )

    def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching query - uses countDocuments for accuracy"""
        try:
            collection = self._get_collection()
            if collection is None:
                return 0

            query = query or {}
            # Use estimated_document_count for empty query (faster on large collections)
            if not query:
                return collection.estimated_document_count()

            return collection.count_documents(query)

        except Exception as e:
            logger.error(f"Error counting CVEs: {e}")
            return 0

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics for monitoring large collections"""
        try:
            collection = self._get_collection()
            if collection is None:
                return {}

            stats = collection.database.command("collStats", collection.name)

            return {
                "total_documents": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "avg_doc_size": stats.get("avgObjSize", 0),
                "indexes": len(list(collection.list_indexes())),
                "total_index_size": stats.get("totalIndexSize", 0)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
