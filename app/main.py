from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time
import logging
import os
from pathlib import Path

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

# Mount static files (add this after the app creation but before middleware)
if settings.DEBUG:
    # Mount static files for development
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Serve the graph visualizer
    @app.get("/visualizer")
    async def serve_visualizer():
        """Serve the knowledge graph visualizer"""
        return FileResponse("static/graph-visualizer.html")

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
    
    try:
        # Test triplestore connection
        from app.dependencies import get_triplestore_client
        from app.core.triplestore_client import TriplestoreClient
        
        triplestore = TriplestoreClient()
        connection_test = await triplestore.test_connection()
        
        if connection_test:
            logger.info("✅ GraphDB triplestore connection established")
            
            # Get triplestore status
            status = await triplestore.get_status()
            triple_count = status.get('triple_count', 0)
            logger.info(f"📊 Current triplestore contains {triple_count} triples")
            
        else:
            logger.error("❌ Failed to connect to GraphDB triplestore")
            
        # Initialize base ontology namespaces (ensure they exist)
        base_prefixes = {
            "wdo": settings.WDO_NAMESPACE,
            "sbekms": settings.INSTANCE_NAMESPACE,
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "dcterms": "http://purl.org/dc/terms/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        }
        
        # Log ontology namespaces
        logger.info("🔗 Ontology namespaces initialized:")
        for prefix, namespace in base_prefixes.items():
            logger.info(f"   {prefix}: {namespace}")
            
        # Initialize semantic annotator
        from app.core.semantic_annotator import SemanticAnnotator
        annotator = SemanticAnnotator()
        logger.info("🔬 Semantic annotator initialized")
        
        # Verify upload directory exists
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Upload directory verified: {upload_dir}")
        
        # Log system configuration
        logger.info("⚙️  System configuration:")
        logger.info(f"   Debug mode: {settings.DEBUG}")
        logger.info(f"   API version: {settings.VERSION}")
        logger.info(f"   Max file size: {settings.MAX_FILE_SIZE} bytes")
        
    except Exception as e:
        logger.error(f"❌ Startup initialization failed: {e}")
        # Don't crash the app, but log the error
        
    logger.info("🚀 SBEKMS Backend API started successfully")

@app.on_event("shutdown") 
async def shutdown_event():
    logger.info("🛑 Shutting down SBEKMS Backend API...")
    
    try:
        # Log final statistics
        from app.core.triplestore_client import TriplestoreClient
        triplestore = TriplestoreClient()
        
        try:
            status = await triplestore.get_status()
            triple_count = status.get('triple_count', 0)
            logger.info(f"📊 Final triplestore state: {triple_count} triples")
        except:
            logger.info("📊 Could not retrieve final triplestore statistics")
            
        # Clean up any temporary resources if needed
        logger.info("🧹 Cleanup completed")
        
    except Exception as e:
        logger.error(f"⚠️  Shutdown cleanup failed: {e}")
        
    logger.info("👋 SBEKMS Backend API shutdown complete")

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