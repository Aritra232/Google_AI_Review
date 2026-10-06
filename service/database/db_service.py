import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("database_service")

class DatabaseService:
    """Manages asynchronous MongoDB connection using Motor."""

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.getenv("DATABASE_URL")
        self.db_name = db_name or os.getenv("DATABASE_NAME")
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> AsyncIOMotorDatabase:
        """Initialize MongoDB client and verify connection."""
        if not self.uri:
            raise ValueError("DATABASE_URL is not configured in environment variables.")
        if not self.db_name:
            raise ValueError("DATABASE_NAME is not configured in environment variables.")

        if self.client is None:
            logger.info("Connecting to MongoDB...")
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            # Quick ping to verify connectivity
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB database: %s", self.db_name)

        return self.db

    async def close(self):
        """Close MongoDB connection pool."""
        if self.client:
            logger.info("Closing MongoDB connection pool...")
            self.client.close()
            self.client = None
            self.db = None

    async def ping(self) -> bool:
        """Check if MongoDB server is responsive."""
        try:
            if self.client:
                await self.client.admin.command("ping")
                return True
            return False
        except Exception as e:
            logger.error("MongoDB ping failed: %s", e)
            return False

    def get_db(self) -> AsyncIOMotorDatabase:
        """Return the active database instance."""
        if self.db is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self.db


# Global singleton instance
_db_service_instance: Optional[DatabaseService] = None

def get_db_service() -> DatabaseService:
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DatabaseService()
    return _db_service_instance

def get_database() -> AsyncIOMotorDatabase:
    return get_db_service().get_db()
