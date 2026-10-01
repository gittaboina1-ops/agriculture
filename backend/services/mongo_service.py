from typing import Dict, Any, List, Optional
import logging
from backend.config import settings

logger = logging.getLogger("mongo_service")

class MongoService:
    def __init__(self):
        self.client = None
        self.connected = False
        self.mongo_error_reason: Optional[str] = None
        self.mock_db = {
            "farmers": [
                {"farmer_id": "FARMER_RAMESH_01", "name": "Ramesh Patel", "region": "South-East Valley", "acreage": 12.5, "primary_crop": "Tomato"},
                {"farmer_id": "FARMER_SITA_02", "name": "Sita Devi", "region": "Northern Hills", "acreage": 8.0, "primary_crop": "Potato"}
            ],
            "query_history": []
        }
        self._init_mongo()

    def _init_mongo(self):
        try:
            import pymongo
            self.client = pymongo.MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.connected = True
            self.mongo_error_reason = None
            logger.info("Successfully connected to live MongoDB instance.")
        except Exception as e:
            self.connected = False
            self.mongo_error_reason = str(e)
            logger.info(f"MongoDB live instance unavailable ({e}). Operating in resilient application mode.")


    def log_query(self, query_record: Dict[str, Any]):
        if self.connected and self.client:
            try:
                db = self.client[settings.MONGODB_DB]
                db.query_history.insert_one(query_record)
                return
            except Exception:
                pass
        self.mock_db["query_history"].append(query_record)

    def get_query_history(self) -> List[Dict[str, Any]]:
        if self.connected and self.client:
            try:
                db = self.client[settings.MONGODB_DB]
                history = list(db.query_history.find({}, {"_id": 0}).sort("timestamp", -1).limit(20))
                return history
            except Exception:
                pass
        return list(reversed(self.mock_db["query_history"][-20:]))

    def get_farmer_profiles(self) -> List[Dict[str, Any]]:
        return self.mock_db["farmers"]

mongo_service = MongoService()
