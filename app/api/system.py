from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.models.common import SuccessResponse, ErrorResponse
from app.dependencies import get_triplestore_client, get_ontology_manager
from app.core.triplestore_client import TriplestoreClient
from app.core.ontology_manager import OntologyManager
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def system_health():
    """System API health check"""
    return {
        "status": "healthy", 
        "service": "system",
        "version": settings.VERSION
    }

@router.get("/status", response_model=SuccessResponse)
async def get_system_status(
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Get comprehensive system status"""
    try:
        # Test triplestore connection
        triplestore_connected = await triplestore.test_connection()
        
        # Get repository status
        repository_exists = False
        repository_stats = None
        if triplestore_connected:
            repository_exists = await triplestore.repository_exists()
            if repository_exists:
                repository_stats = await triplestore.get_repository_stats()
        
        # Get ontology status
        ontology_stats = await ontology_manager.get_ontology_stats()
        
        status_data = {
            "system": {
                "version": settings.VERSION,
                "debug": settings.DEBUG,
                "log_level": settings.LOG_LEVEL
            },
            "triplestore": {
                "url": settings.TRIPLESTORE_URL,
                "repository": settings.TRIPLESTORE_REPOSITORY,
                "connected": triplestore_connected,
                "repository_exists": repository_exists,
                "stats": repository_stats
            },
            "ontology": ontology_stats,
            "configuration": {
                "upload_dir": settings.UPLOAD_DIR,
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_extensions": settings.ALLOWED_EXTENSIONS[:5]  # Show first 5
            }
        }
        
        return SuccessResponse(
            message="System status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.post("/initialize", response_model=SuccessResponse)
async def initialize_system(
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Initialize the complete SBEKMS system"""
    try:
        initialization_results = {}
        
        # Initialize triplestore
        logger.info("Initializing triplestore...")
        triplestore_success = await triplestore.initialize()
        initialization_results["triplestore"] = {
            "success": triplestore_success,
            "message": "Triplestore initialized successfully" if triplestore_success 
                      else "Triplestore initialization failed"
        }
        
        # Load ontology
        logger.info("Loading ontology...")
        ontology_success = await ontology_manager.load_ontology()
        initialization_results["ontology"] = {
            "success": ontology_success,
            "message": "Ontology loaded successfully" if ontology_success 
                      else "Ontology loading failed"
        }
        
        # Overall success
        overall_success = triplestore_success and ontology_success
        
        if not overall_success:
            raise HTTPException(
                status_code=500, 
                detail=f"System initialization failed: {initialization_results}"
            )
        
        # Get updated stats after initialization
        ontology_stats = await ontology_manager.get_ontology_stats()
        repository_stats = await triplestore.get_repository_stats()
        
        return SuccessResponse(
            message="System initialized successfully",
            data={
                "initialization": initialization_results,
                "ontology_stats": ontology_stats,
                "repository_stats": repository_stats
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"System initialization failed: {str(e)}")

@router.get("/triplestore/stats", response_model=SuccessResponse)
async def get_triplestore_stats(
    triplestore: TriplestoreClient = Depends(get_triplestore_client)
):
    """Get detailed triplestore statistics"""
    try:
        stats = await triplestore.get_repository_stats()
        return SuccessResponse(
            message="Triplestore statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Failed to get triplestore stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get triplestore stats: {str(e)}")

@router.get("/ontology/stats", response_model=SuccessResponse)
async def get_ontology_stats(
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Get detailed ontology statistics"""
    try:
        stats = await ontology_manager.get_ontology_stats()
        return SuccessResponse(
            message="Ontology statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Failed to get ontology stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology stats: {str(e)}")

@router.get("/ontology/classes", response_model=SuccessResponse)
async def get_ontology_classes(
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Get all ontology classes"""
    try:
        if not ontology_manager.loaded:
            raise HTTPException(status_code=400, detail="Ontology not loaded. Please initialize the system first.")
        
        classes = ontology_manager.get_classes()
        return SuccessResponse(
            message=f"Retrieved {len(classes)} ontology classes",
            data={"classes": classes}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ontology classes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology classes: {str(e)}")

@router.get("/ontology/properties", response_model=SuccessResponse)
async def get_ontology_properties(
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Get all ontology properties"""
    try:
        if not ontology_manager.loaded:
            raise HTTPException(status_code=400, detail="Ontology not loaded. Please initialize the system first.")
        
        properties = ontology_manager.get_properties()
        return SuccessResponse(
            message=f"Retrieved {len(properties)} ontology properties",
            data={"properties": properties}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ontology properties: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology properties: {str(e)}")

@router.get("/ontology/hierarchy", response_model=SuccessResponse)
async def get_ontology_hierarchy(
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Get ontology class hierarchy"""
    try:
        if not ontology_manager.loaded:
            raise HTTPException(status_code=400, detail="Ontology not loaded. Please initialize the system first.")
        
        hierarchy = ontology_manager.get_class_hierarchy()
        return SuccessResponse(
            message="Ontology hierarchy retrieved successfully",
            data=hierarchy
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ontology hierarchy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology hierarchy: {str(e)}")

@router.delete("/triplestore/clear", response_model=SuccessResponse)
async def clear_triplestore(
    triplestore: TriplestoreClient = Depends(get_triplestore_client)
):
    """Clear all data from triplestore (development/testing only)"""
    try:
        if not settings.DEBUG:
            raise HTTPException(status_code=403, detail="This operation is only allowed in debug mode")
        
        success = await triplestore.clear_repository()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear triplestore")
        
        return SuccessResponse(
            message="Triplestore cleared successfully",
            data={"cleared": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear triplestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear triplestore: {str(e)}") 