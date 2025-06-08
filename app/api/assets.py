from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import uuid
import aiofiles
import os
from pathlib import Path
from datetime import datetime
import logging
import hashlib
from app.core.semantic_annotator import SemanticAnnotator

from app.models.common import SuccessResponse, ErrorResponse, PaginationParams
from app.models.assets import AssetMetadata, AssetResponse, AssetListResponse, UploadAssetRequest, AssetType
from app.config import settings
from app.dependencies import get_triplestore_client, get_ontology_manager
from app.core.triplestore_client import TriplestoreClient
from app.core.ontology_manager import OntologyManager
# from app.core.semantic_annotator import *

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def assets_health():
    """Assets API health check"""
    return {"status": "healthy", "service": "assets"}

@router.post("/upload", response_model=SuccessResponse)
async def upload_asset(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    project_name: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    """Upload and process a knowledge asset"""
    try:
        # Generate unique ID
        asset_id = str(uuid.uuid4())
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / f"{asset_id}_{file.filename}"
        content = await file.read()
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Create basic metadata
        file_extension = Path(file.filename).suffix.lower()
        
        # Determine asset type
        asset_type = AssetType.UNKNOWN
        if file_extension in ['.py', '.js', '.ts', '.java', '.cpp']:
            asset_type = AssetType.SOURCE_CODE
        elif file_extension in ['.md', '.txt', '.rst', '.pdf']:
            asset_type = AssetType.DOCUMENTATION
        elif file_extension in ['.json', '.yml', '.yaml', '.toml']:
            asset_type = AssetType.CONFIGURATION
        elif file_extension in ['.png', '.jpg', '.svg', '.css']:
            asset_type = AssetType.ASSET_FILE
        
        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # Enhanced WDO classification
        wdo_classes = ["DigitalInformationCarrier"]
        if asset_type == AssetType.SOURCE_CODE:
            wdo_classes.append("SourceCodeFile")
            if file_extension == '.py':
                wdo_classes.append("PythonSourceCodeFile")
            elif file_extension in ['.js', '.ts']:
                wdo_classes.append("JavaScriptSourceCodeFile")
            elif file_extension == '.java':
                wdo_classes.append("JavaSourceCodeFile")
        elif asset_type == AssetType.DOCUMENTATION:
            wdo_classes.append("DocumentationFile")
        elif asset_type == AssetType.CONFIGURATION:
            wdo_classes.append("ConfigurationFile")
        elif asset_type == AssetType.ASSET_FILE:
            wdo_classes.append("AssetFile")
        
        # Create metadata
        metadata = AssetMetadata(
            id=asset_id,
            file_name=file.filename,
            file_size=len(content),
            file_extension=file_extension,
            mime_type=file.content_type or "application/octet-stream",
            checksum=checksum,
            asset_type=asset_type,
            line_count=len(content.decode('utf-8', errors='ignore').split('\n')),
            character_count=len(content),
            created_at=datetime.now(),
            title=title,
            description=description,
            tags=tag_list,
            project_name=project_name,
            author=author,
            wdo_classes=wdo_classes
        )
        
        # Generate and store RDF triples
        semantic_annotator = SemanticAnnotator()
        rdf_triples_count = await semantic_annotator.annotate_asset(
            metadata.dict(), triplestore
        )
        
        # Update metadata with RDF count
        metadata.rdf_triples_count = rdf_triples_count
        
        return SuccessResponse(
            message=f"Asset '{file.filename}' uploaded and annotated successfully",
            data={
                "asset_id": asset_id,
                "file_name": file.filename,
                "file_size": len(content),
                "asset_type": asset_type,
                "wdo_classes": wdo_classes,
                "rdf_triples_count": rdf_triples_count,
                "checksum": checksum,
                "metadata": metadata.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to upload asset: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/list", response_model=SuccessResponse)
async def list_assets(
    page: int = 1,
    per_page: int = 20,
    asset_type: Optional[AssetType] = None,
    project_name: Optional[str] = None
):
    """List uploaded assets with pagination"""
    try:
        # TODO: Implement actual database storage
        # For now, return empty list
        return SuccessResponse(
            message="Assets retrieved successfully",
            data={
                "assets": [],
                "total": 0,
                "page": page,
                "per_page": per_page
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list assets: {str(e)}")

@router.get("/{asset_id}", response_model=SuccessResponse)
async def get_asset(asset_id: str):
    """Get asset by ID"""
    try:
        # TODO: Implement actual asset retrieval
        raise HTTPException(status_code=404, detail="Asset not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get asset: {str(e)}")
