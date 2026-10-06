import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from service.database.db_service import get_database

logger = logging.getLogger("company_service")


class CompanyService:
    """Service to fetch and process company information from MongoDB."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is not None:
            return self._db
        return get_database()

    def _parse_object_id(self, id_str: str) -> ObjectId:
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid company_id format: '{id_str}'. Must be a valid 24-character hex MongoDB ObjectId."
            )

    async def get_company_by_id(self, company_id: str) -> Dict[str, Any]:
        """
        Fetch company details by company_id.
        First searches BusinessProfile collection, then falls back to User collection.
        """
        obj_id = self._parse_object_id(company_id)

        # 1. Look in BusinessProfile collection
        company_doc = await self.db["BusinessProfile"].find_one({"_id": obj_id})
        if company_doc:
            return {
                "id": str(company_doc.get("_id")),
                "name": company_doc.get("name") or "Our Business",
                "category": company_doc.get("category") or "General Services",
                "address": company_doc.get("address"),
                "phone": company_doc.get("phone"),
                "website": company_doc.get("website"),
                "review_url": company_doc.get("googleReviewUrl") or company_doc.get("googleMapsUrl") or company_doc.get("website"),
                "google_review_url": company_doc.get("googleReviewUrl"),
                "google_maps_url": company_doc.get("googleMapsUrl"),
                "rating": company_doc.get("rating"),
                "user_ratings_total": company_doc.get("userRatingsTotal"),
                "source": "BusinessProfile"
            }

        # 2. Fallback: Look in User collection
        user_doc = await self.db["User"].find_one({"_id": obj_id})
        if user_doc:
            return {
                "id": str(user_doc.get("_id")),
                "name": user_doc.get("name") or "Our Company",
                "category": "Service Provider",
                "address": None,
                "phone": None,
                "website": None,
                "review_url": None,
                "google_review_url": None,
                "google_maps_url": None,
                "rating": None,
                "user_ratings_total": None,
                "source": "User"
            }

        raise HTTPException(
            status_code=404,
            detail=f"Company with ID '{company_id}' was not found in database."
        )

    async def list_companies(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List companies from BusinessProfile collection."""
        cursor = self.db["BusinessProfile"].find().limit(limit)
        companies = []
        async for doc in cursor:
            companies.append({
                "id": str(doc.get("_id")),
                "name": doc.get("name"),
                "category": doc.get("category"),
                "address": doc.get("address"),
                "phone": doc.get("phone"),
                "website": doc.get("website"),
                "review_url": doc.get("googleReviewUrl") or doc.get("googleMapsUrl")
            })
        return companies
