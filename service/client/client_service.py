import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from service.database.db_service import get_database

logger = logging.getLogger("client_service")


class ClientService:
    """Service to fetch and process client/customer information from MongoDB."""

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
                detail=f"Invalid client_id format: '{id_str}'. Must be a valid 24-character hex MongoDB ObjectId."
            )

    async def get_client_by_id(self, client_id: str) -> Dict[str, Any]:
        """
        Fetch client details by client_id.
        Searches Campaign collection (which stores customer campaign entries),
        then falls back to User, Client, or Customer collections.
        """
        obj_id = self._parse_object_id(client_id)

        # 1. Look in Campaign collection (client review campaign records)
        campaign_doc = await self.db["Campaign"].find_one({"_id": obj_id})
        if campaign_doc:
            return {
                "id": str(campaign_doc.get("_id")),
                "name": campaign_doc.get("customerName") or "Valued Client",
                "phone": campaign_doc.get("customerPhone"),
                "email": campaign_doc.get("customerEmail"),
                "channel": campaign_doc.get("channel") or "SMS",
                "status": campaign_doc.get("status"),
                "short_code": campaign_doc.get("shortCode"),
                "company_id": str(campaign_doc.get("businessId")) if campaign_doc.get("businessId") else None,
                "source": "Campaign"
            }

        # 2. Check if a dedicated 'Client' or 'Customer' collection exists
        for col_name in ["Client", "Customer", "clients", "customers"]:
            col_doc = await self.db[col_name].find_one({"_id": obj_id})
            if col_doc:
                return {
                    "id": str(col_doc.get("_id")),
                    "name": col_doc.get("name") or col_doc.get("fullName") or "Valued Client",
                    "phone": col_doc.get("phone") or col_doc.get("mobile"),
                    "email": col_doc.get("email"),
                    "channel": col_doc.get("channel") or "SMS",
                    "status": col_doc.get("status"),
                    "short_code": None,
                    "company_id": str(col_doc.get("businessId") or col_doc.get("companyId")) if (col_doc.get("businessId") or col_doc.get("companyId")) else None,
                    "source": col_name
                }

        # 3. Fallback: Look in User collection
        user_doc = await self.db["User"].find_one({"_id": obj_id})
        if user_doc:
            return {
                "id": str(user_doc.get("_id")),
                "name": user_doc.get("name") or "Valued Client",
                "phone": None,
                "email": user_doc.get("email"),
                "channel": "Email",
                "status": user_doc.get("status"),
                "short_code": None,
                "company_id": None,
                "source": "User"
            }

        raise HTTPException(
            status_code=404,
            detail=f"Client with ID '{client_id}' was not found in database."
        )

    async def list_clients(self, company_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List clients from Campaign collection, optionally filtered by company_id."""
        query = {}
        if company_id:
            try:
                query["businessId"] = ObjectId(company_id)
            except Exception:
                query["businessId"] = company_id

        cursor = self.db["Campaign"].find(query).limit(limit)
        clients = []
        async for doc in cursor:
            clients.append({
                "id": str(doc.get("_id")),
                "name": doc.get("customerName"),
                "phone": doc.get("customerPhone"),
                "email": doc.get("customerEmail"),
                "channel": doc.get("channel"),
                "status": doc.get("status"),
                "company_id": str(doc.get("businessId")) if doc.get("businessId") else None
            })
        return clients
