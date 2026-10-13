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
from service.competitor.competitor_service import CompetitorService
from service.analytics.gap_service import ReviewGapService
from service.report.monthly_report_service import MonthlyReportService

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
    title="Client Review & Competitor AI Intelligence Platform",
    description="FastAPI service powered by DeepSeek AI and MongoDB for review requests, automated competitor intelligence, review gap analysis, and visual monthly reports.",
    version="2.0.0",
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

# Core Service instances
company_service = CompanyService()
client_service = ClientService()
ai_service = DeepSeekService()
review_service = ReviewService(
    company_service=company_service,
    client_service=client_service,
    ai_service=ai_service
)
competitor_service = CompetitorService(ai_service=ai_service)
gap_service = ReviewGapService(ai_service=ai_service)
monthly_report_service = MonthlyReportService(ai_service=ai_service)


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


class CompetitorIntelligenceRequest(BaseModel):
    """Payload for competitor intelligence & automated competitor discovery."""
    business_id: str = Field(
        ...,
        description="MongoDB ObjectId of the business",
        example="6ac0774ee0c1a4a1692696ce"
    )
    radius_miles: Optional[int] = Field(
        5,
        description="Radius in miles to search for competitors (e.g. 5, 10)",
        example=5
    )
    limit: Optional[int] = Field(
        None,
        description="Number of competitors (3, 5, or 10 based on subscription plan)",
        example=5
    )
    auto_identify: Optional[bool] = Field(
        False,
        description="Whether to use DeepSeek AI to automatically identify new local competitors",
        example=False
    )


class ReviewGapRequest(BaseModel):
    """Payload for review gap and competitive comparison analysis."""
    business_id: str = Field(
        ...,
        description="MongoDB ObjectId of the business",
        example="6ac0774ee0c1a4a1692696ce"
    )


class MonthlyReportRequest(BaseModel):
    """Payload for monthly growth AI email report generation."""
    business_id: str = Field(
        ...,
        description="MongoDB ObjectId of the business",
        example="6ac0774ee0c1a4a1692696ce"
    )
    month: Optional[str] = Field(
        None,
        description="Month name for the report (e.g. 'October')",
        example="October"
    )
    year: Optional[int] = Field(
        None,
        description="Year for the report (e.g. 2026)",
        example=2026
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
# SECTION 4: API ROUTES
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


# Route 2: Generate Review Request Message
@app.post(
    "/api/generate-review-message",
    tags=["Review Generator"],
    summary="Generate review message using company_id and client_id"
)
async def generate_review_message(payload: ReviewMessageRequest):
    """
    1. Fetches company information from MongoDB using company_id.
    2. Fetches client information from MongoDB using client_id.
    3. Prompts DeepSeek AI to generate a polite, engaging review request message.
    """
    try:
        result = await review_service.generate_review_request(
            company_id=payload.company_id,
            client_id=payload.client_id
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


# Route 3: Competitor Intelligence & Identification
@app.post(
    "/api/competitors/intelligence",
    tags=["Competitor Intelligence"],
    summary="Get competitor intelligence and automated competitor discovery"
)
async def get_competitor_intelligence(payload: CompetitorIntelligenceRequest):
    """
    Analyzes local competitors within radius (5-10 miles) based on business category & location.
    Calculates review volumes, growth rates, market positioning, and provides AI strategic summary.
    """
    try:
        result = await competitor_service.get_competitor_intelligence(
            business_id=payload.business_id,
            radius_miles=payload.radius_miles or 5,
            limit=payload.limit,
            auto_identify=payload.auto_identify or False
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching competitor intelligence: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch competitor intelligence: {str(e)}"
        )


# Route 4: Review Gap Analysis
@app.post(
    "/api/review-gap/analyze",
    tags=["Review Gap Analysis"],
    summary="Analyze review gap compared to competitors"
)
async def analyze_review_gap(payload: ReviewGapRequest):
    """
    Compares client's review volume, rating, and growth percentage with nearby competitors.
    Returns gap percentage (+/- Ahead or Behind) and DeepSeek AI strategic action plan.
    """
    try:
        result = await gap_service.analyze_review_gap(business_id=payload.business_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error analyzing review gap: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze review gap: {str(e)}"
        )


# Route 5: Monthly AI Growth Report
@app.post(
    "/api/reports/monthly-growth",
    tags=["Monthly AI Report"],
    summary="Generate visual & motivational monthly growth report"
)
async def generate_monthly_growth_report(payload: MonthlyReportRequest):
    """
    Generates monthly summary report featuring:
    - New reviews gained this month
    - Total NFC taps recorded
    - Competitor rank position
    - DeepSeek AI visual & motivational email summary (🟢 Green signal, 👍 Thumbs up, etc.)
    """
    try:
        result = await monthly_report_service.generate_monthly_report(
            business_id=payload.business_id,
            month=payload.month,
            year=payload.year
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error generating monthly report: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate monthly report: {str(e)}"
        )


# Route 6: Preview Message (Direct Test Endpoint)
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
    host = os.getenv("HOST", "127.0.1.0")
    print(f"Starting FastAPI server on http://{host}:{port} ...")
    uvicorn.run("app:app", host=host, port=port, reload=True)
