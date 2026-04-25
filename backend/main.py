<<<<<<< HEAD
"""
Main FastAPI Application

Entry point for the TE Legal Platform backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from config.settings import get_settings
from shared.database.db import init_db
from services.auth.routes.auth_routes import router as auth_router
from services.contracts.routes.contract_routes import router as contract_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant legal technology platform with AI assistance",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
=======
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.contracts import router as contracts_router
from workers.contract.celery_config import celery_app

# ==============================================================================
# LIFECYCLE EVENTS
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage FastAPI app lifecycle.
    """
    # Startup
    print("Starting FastAPI application...")
    yield
    # Shutdown
    print("Shutting down FastAPI application...")


# ==============================================================================
# FASTAPI APP CONFIGURATION
# ==============================================================================

app = FastAPI(
    title="Contract Processing API",
    description="API for uploading PDFs, parsing them to markdown, and analyzing with AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
>>>>>>> f5ce65d2614d833bdcb11f81974de58fc266fd04
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup"""
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


# Include routers
app.include_router(auth_router)
app.include_router(contract_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


if __name__ == "__main__":
    import uvicorn
=======
# ==============================================================================
# ROUTES
# ==============================================================================

# Include contracts routes
app.include_router(contracts_router)


# ==============================================================================
# HEALTH CHECK ENDPOINTS
# ==============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "contract-processor"}


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "Contract Processing API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/contracts/upload",
            "result": "/api/contracts/result/{company_name}",
            "results_list": "/api/contracts/result-list",
            "health": "/health",
            "docs": "/docs"
        }
    }


# ==============================================================================
# APP STARTUP
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
>>>>>>> f5ce65d2614d833bdcb11f81974de58fc266fd04
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
<<<<<<< HEAD
        reload=settings.DEBUG
=======
        reload=True,
        log_level="info"
>>>>>>> f5ce65d2614d833bdcb11f81974de58fc266fd04
    )
