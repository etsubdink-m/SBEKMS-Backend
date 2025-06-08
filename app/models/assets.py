from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AssetType(str, Enum):
    SOURCE_CODE = "source_code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    ASSET_FILE = "asset_file"
    UNKNOWN = "unknown"

class UploadAssetRequest(BaseModel):
    """Request model for asset upload"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    project_name: Optional[str] = None
    author: Optional[str] = None

class AssetMetadata(BaseModel):
    """Asset metadata model"""
    id: str
    file_name: str
    file_size: int
    file_extension: str
    mime_type: str
    checksum: str
    asset_type: AssetType
    programming_language: Optional[str] = None
    
    # Content analysis
    line_count: int = 0
    character_count: int = 0
    function_count: int = 0
    class_count: int = 0
    
    # Semantic annotation
    wdo_classes: List[str] = []
    rdf_triples_count: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # User metadata
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    project_name: Optional[str] = None
    author: Optional[str] = None

class AssetResponse(BaseModel):
    """Response model for asset operations"""
    asset: AssetMetadata
    message: str
    
class AssetListResponse(BaseModel):
    """Response model for asset listing"""
    assets: List[AssetMetadata]
    total: int
    page: int
    per_page: int
