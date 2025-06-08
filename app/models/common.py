from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime, date
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"

class BaseResponse(BaseModel):
    """Base response model"""
    status: ResponseStatus
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class SuccessResponse(BaseResponse):
    """Success response model"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PaginationParams(BaseModel):
    """Pagination parameters"""
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total: int
    offset: int
    limit: int
    has_next: bool
    has_prev: bool

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: float

class SearchQuery(BaseModel):
    """Basic search query model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    search_type: Literal["semantic", "textual", "hybrid"] = Field("hybrid", description="Type of search to perform")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

class AdvancedSearchQuery(SearchQuery):
    """Advanced search query with filters"""
    file_types: Optional[List[str]] = Field(None, description="Filter by file types (py, md, json, etc.)")
    wdo_classes: Optional[List[str]] = Field(None, description="Filter by WDO ontology classes")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    author: Optional[str] = Field(None, description="Filter by author")
    date_from: Optional[date] = Field(None, description="Filter by creation date from")
    date_to: Optional[date] = Field(None, description="Filter by creation date to")
    min_file_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_file_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    has_content: Optional[bool] = Field(None, description="Filter files with/without content analysis")

class SearchResult(BaseModel):
    """Individual search result"""
    asset_id: str
    file_name: str
    title: Optional[str] = None
    description: Optional[str] = None
    file_type: str
    mime_type: str
    file_size: int
    author: Optional[str] = None
    tags: List[str] = []
    wdo_classes: List[str] = []
    created_at: datetime
    relevance_score: float = Field(ge=0.0, le=1.0, description="Search relevance score")
    highlights: List[str] = Field([], description="Highlighted text snippets")

class SearchResponse(BaseResponse):
    """Search results response"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Dict[str, Any]] = None
    results: List[SearchResult] = []
    total_results: int = 0
    search_time_ms: float = 0.0
    suggestions: List[str] = []

class GraphSearchQuery(BaseModel):
    """Knowledge graph search query"""
    entity: str = Field(..., description="Entity to search for")
    relationship_types: Optional[List[str]] = Field(None, description="Types of relationships to explore")
    depth: int = Field(2, ge=1, le=5, description="Search depth in the graph")
    include_ontology: bool = Field(True, description="Include ontological relationships")

class GraphNode(BaseModel):
    """Knowledge graph node"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    """Knowledge graph edge"""
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any] = {}

class GraphSearchResponse(BaseResponse):
    """Knowledge graph search response"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    center_node: str
    query_depth: int

class GraphQuery(BaseModel):
    """Graph query model for different visualization needs"""
    query_type: Literal["neighborhood", "path", "cluster", "full"] = Field("neighborhood", description="Type of graph query")
    center_entity: Optional[str] = Field(None, description="Central entity for neighborhood queries")
    source_entity: Optional[str] = Field(None, description="Source entity for path queries")
    target_entity: Optional[str] = Field(None, description="Target entity for path queries")
    depth: int = Field(2, ge=1, le=5, description="Maximum depth to explore")
    relationship_filters: Optional[List[str]] = Field(None, description="Filter by relationship types")
    node_type_filters: Optional[List[str]] = Field(None, description="Filter by node types")
    include_literals: bool = Field(False, description="Include literal values as nodes")
    max_nodes: int = Field(100, ge=10, le=1000, description="Maximum number of nodes to return")

class GraphAnalytics(BaseModel):
    """Graph analytics and statistics"""
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    relationship_types: Dict[str, int]
    avg_degree: float
    max_degree: int
    connected_components: int
    density: float

class GraphVisualization(BaseModel):
    """Graph visualization configuration"""
    layout: Literal["force", "circular", "hierarchical", "grid"] = Field("force", description="Layout algorithm")
    node_size_by: Optional[str] = Field(None, description="Property to determine node size")
    node_color_by: Optional[str] = Field("type", description="Property to determine node color")
    edge_thickness_by: Optional[str] = Field(None, description="Property to determine edge thickness")
    clustering: bool = Field(True, description="Enable node clustering")
    physics: bool = Field(True, description="Enable physics simulation")

class KnowledgeGraphResponse(BaseResponse):
    """Complete knowledge graph response"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    graph: Dict[str, Any] = {}  # Contains nodes and edges
    analytics: Optional[GraphAnalytics] = None
    visualization_config: Optional[GraphVisualization] = None
    query_info: Dict[str, Any] = {} 