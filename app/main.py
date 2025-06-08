from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.config import settings
from app.api import users, assets, search, graph, ontology, sparql, system

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Semantic-Based Explicit Knowledge Management System Backend API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting SBEKMS Backend API...")
    
    # TODO: Initialize semantic components
    # - Load ontology
    # - Test triplestore connection
    # - Initialize parsers
    
    logger.info("SBEKMS Backend API started successfully")

@app.on_event("shutdown") 
async def shutdown_event():
    logger.info("Shutting down SBEKMS Backend API...")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": time.time()
    }

# Include API routers
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"]
)

app.include_router(
    assets.router,
    prefix=f"{settings.API_V1_PREFIX}/assets", 
    tags=["assets"]
)

app.include_router(
    search.router,
    prefix=f"{settings.API_V1_PREFIX}/search",
    tags=["search"]
)

app.include_router(
    graph.router,
    prefix=f"{settings.API_V1_PREFIX}/graph",
    tags=["knowledge-graph"]
)

app.include_router(
    ontology.router,
    prefix=f"{settings.API_V1_PREFIX}/ontology",
    tags=["ontology"]
)

app.include_router(
    sparql.router,
    prefix=f"{settings.API_V1_PREFIX}/sparql",
    tags=["sparql"]
)

app.include_router(
    system.router,
    prefix=f"{settings.API_V1_PREFIX}/system",
    tags=["system"]
)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "SBEKMS Backend API",
        "version": settings.VERSION,
        "docs_url": "/docs" if settings.DEBUG else None,
        "health_url": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 