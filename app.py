import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from service.database.db_service import get_db_service
from service.company.company_service import CompanyService
from service.client.client_service import ClientService
from service.ai.deepseek_service import DeepSeekService
from service.review.review_service import ReviewService

load_dotenv()

# ==============================================================================
# SECTION 1: LOGGING & CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")


# ==============================================================================
# SECTION 2: DATABASE LIFECYCLE & APP SETUP
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown of MongoDB connection."""
    logger.info("Initializing database connection...")
    db_service = get_db_service()
    try:
        await db_service.connect()
        logger.info("Database connected successfully.")
    except Exception as e:
        logger.error("Database connection failed on startup: %s", e)
    yield
    logger.info("Shutting down database connection...")
    await db_service.close()


app = FastAPI(
    title="Client Review Request AI Service",
    description="FastAPI service that fetches company and client details from MongoDB and uses DeepSeek AI to generate polite review request messages.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances
company_service = CompanyService()
client_service = ClientService()
ai_service = DeepSeekService()
review_service = ReviewService(
    company_service=company_service,
    client_service=client_service,
    ai_service=ai_service
)


# ==============================================================================
# SECTION 3: REQUEST SCHEMAS (PYDANTIC)
# ==============================================================================

class ReviewMessageRequest(BaseModel):
    """Payload for generating review request by company_id and client_id."""
    company_id: str = Field(
        ...,
        description="MongoDB ObjectId of the company (from BusinessProfile collection)",
        example="6ac0774ee0c1a4a1692696ce"
    )
    client_id: str = Field(
        ...,
        description="MongoDB ObjectId of the client (from Campaign collection)",
        example="6ac0866de0c1a4a1692696d8"
    )
    service_name: Optional[str] = Field(
        None,
        description="Optional name of the service availed (e.g. 'Lunch & Coffee')",
        example="Lunch & Coffee"
    )
    channel: Optional[str] = Field(
        "SMS",
        description="Communication channel: 'SMS', 'WhatsApp', or 'Email'",
        example="SMS"
    )
    tone: Optional[str] = Field(
        "friendly and polite",
        description="Desired message tone (e.g. 'friendly', 'polite', 'casual', 'formal')",
        example="friendly and polite"
    )
    language: Optional[str] = Field(
        "English",
        description="Language for the message (e.g. 'English', 'Bengali')",
        example="English"
    )
    custom_instructions: Optional[str] = Field(
        None,
        description="Optional extra instructions for AI generation",
        example="Keep it short and warm"
    )


class PreviewMessageRequest(BaseModel):
    """Payload for previewing message directly without querying database IDs."""
    company_name: str = Field(..., example="Bella's Cafe House")
    company_category: Optional[str] = Field("Cafe / Restaurant", example="Cafe / Restaurant")
    review_url: Optional[str] = Field(None, example="https://g.page/r/CbellascafeABCDEFG")
    client_name: str = Field(..., example="Sarah Mitchell")
    service_name: Optional[str] = Field(None, example="Dinner Service")
    channel: Optional[str] = Field("SMS", example="SMS")
    tone: Optional[str] = Field("friendly and polite", example="friendly and polite")
    language: Optional[str] = Field("English", example="English")
    custom_instructions: Optional[str] = Field(None, example="Be very brief")


# ==============================================================================
# SECTION 4: API ROUTES (3 ESSENTIAL ENDPOINTS)
# ==============================================================================

# Route 1: Health Check
@app.get("/health", tags=["Health & Status"], summary="Check API & DB health")
async def health_check():
    """Verify server status, MongoDB connectivity, and DeepSeek key availability."""
    db_ok = await get_db_service().ping()
    deepseek_configured = bool(os.getenv("DEEPSEEK_API_KEY"))

    status_code = status.HTTP_200_OK if db_ok and deepseek_configured else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if (db_ok and deepseek_configured) else "unhealthy",
        "database_connected": db_ok,
        "deepseek_configured": deepseek_configured,
        "database_name": os.getenv("DATABASE_NAME"),
        "port": int(os.getenv("PORT", 2000))
    }


# Route 2: Generate Review Request (Core Endpoint)
@app.post(
    "/api/generate-review-message",
    tags=["Review Generator"],
    summary="Generate review message using company_id and client_id"
)
async def generate_review_message(payload: ReviewMessageRequest):
    """
    Core business endpoint:
    1. Fetches company information from MongoDB using company_id.
    2. Fetches client information from MongoDB using client_id.
    3. Prompts DeepSeek AI to generate a polite, engaging review request message.
    """
    try:
        result = await review_service.generate_review_request(
            company_id=payload.company_id,
            client_id=payload.client_id,
            service_name=payload.service_name,
            channel=payload.channel,
            tone=payload.tone,
            language=payload.language,
            custom_instructions=payload.custom_instructions
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error generating review message: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate review request: {str(e)}"
        )


# Route 3: Preview Message (Direct Test Endpoint)
@app.post(
    "/api/preview-message",
    tags=["Review Generator"],
    summary="Preview message directly with custom details (no DB query required)"
)
async def preview_message(payload: PreviewMessageRequest):
    """Test AI message generation on-the-fly without needing existing database IDs."""
    company_mock = {
        "name": payload.company_name,
        "category": payload.company_category,
        "review_url": payload.review_url
    }
    client_mock = {
        "name": payload.client_name,
        "channel": payload.channel
    }

    prompt = review_service._build_prompt(
        company=company_mock,
        client=client_mock,
        service_name=payload.service_name,
        channel=payload.channel,
        tone=payload.tone,
        language=payload.language,
        custom_instructions=payload.custom_instructions
    )

    ai_resp = await ai_service.generate_chat_completion(
        messages=[
            {
                "role": "system",
                "content": "You are a professional customer experience copywriter crafting review request messages."
            },
            {"role": "user", "content": prompt}
        ]
    )

    return {
        "success": True,
        "generated_message": ai_resp.get("content"),
        "model": ai_resp.get("model"),
        "usage": ai_resp.get("usage")
    }


# ==============================================================================
# SECTION 5: SERVER ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 2000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting FastAPI server on http://{host}:{port} ...")
    uvicorn.run("app:app", host=host, port=port, reload=True)
