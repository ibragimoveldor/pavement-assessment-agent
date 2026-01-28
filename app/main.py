# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import analyze_router, chat_router
from app.database import Base, engine

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("\n" + "="*60)
    print("🚀 Starting Pavement Assessment AI Agent")
    print("="*60)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
    
    # Test AWS Bedrock (optional)
    try:
        from app.core.aws_bedrock import get_bedrock_client
        bedrock = get_bedrock_client()
        print("✅ AWS Bedrock client ready")
    except Exception as e:
        print(f"⚠️  AWS Bedrock not configured: {e}")
        print("   (Fallback mode will be used)")
    
    print("="*60 + "\n")
    
    yield
    
    # Shutdown
    print("\n👋 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    ## Pavement Assessment AI Agent
    
    AI-powered pavement condition assessment using:
    - **YOLO** for defect detection
    - **AWS Bedrock (Claude)** for AI analysis
    - **LangGraph** for multi-step reasoning
    - **FastAPI** for robust API
    
    ### Features:
    - Upload pavement images for instant PCI scoring
    - AI-powered defect analysis and recommendations
    - Natural language chat about assessment results
    - Cost estimation and repair timelines
    
    ### Workflow:
    1. Upload image → YOLO detection
    2. Calculate PCI score
    3. AI analysis with Claude (AWS Bedrock)
    4. Chat with AI about results
    """,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    analyze_router,
    prefix="/api/v1",
    tags=["Analysis"]
)

app.include_router(
    chat_router,
    prefix="/api/v1",
    tags=["Chat"]
)

# Root endpoint
@app.get("/")
async def root():
    """API root - health check and info"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "chat": "POST /api/v1/chat",
            "assessment": "GET /api/v1/assessment/{id}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.api_version
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )