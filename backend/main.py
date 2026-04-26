from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.contracts import router as contracts_router
from routes.auth import router as auth_router
from workers.contract.celery_config import celery_app
from models.database import init_db_indexes

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
    init_db_indexes()
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# ROUTES
# ==============================================================================

# Include contracts routes
app.include_router(contracts_router)
app.include_router(auth_router)


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
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
