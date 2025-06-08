from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
import time
from datetime import datetime, date

from app.models.common import (
    SearchResponse, SearchResult, SuccessResponse, ResponseStatus
)
from app.core.triplestore_client import TriplestoreClient
from app.core.ontology_manager import OntologyManager
from app.dependencies import get_triplestore_client, get_ontology_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# Unified Search Request Model
from pydantic import BaseModel, Field
from typing import Literal

class UnifiedSearchQuery(BaseModel):
    """Unified search query that handles both basic and advanced search"""
    # Required fields
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    
    # Basic search options
    search_type: Literal["semantic", "textual", "hybrid"] = Field("hybrid", description="Type of search to perform")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    # Advanced search filters (all optional)
    file_types: Optional[List[str]] = Field(None, description="Filter by file types (py, md, json, etc.)")
    wdo_classes: Optional[List[str]] = Field(None, description="Filter by WDO ontology classes")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    author: Optional[str] = Field(None, description="Filter by author")
    date_from: Optional[date] = Field(None, description="Filter by creation date from")
    date_to: Optional[date] = Field(None, description="Filter by creation date to")
    min_file_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_file_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    has_content: Optional[bool] = Field(None, description="Filter files with/without content analysis")
    
    def has_advanced_filters(self) -> bool:
        """Check if any advanced filters are provided"""
        return any([
            self.file_types, self.wdo_classes, self.tags, self.author,
            self.date_from, self.date_to, self.min_file_size, 
            self.max_file_size, self.has_content is not None
        ])


class UnifiedSearchService:
    """Unified search service that automatically handles basic and advanced search"""
    
    def __init__(self, triplestore: TriplestoreClient, ontology: OntologyManager):
        self.triplestore = triplestore
        self.ontology = ontology
        self.WDO_NS = "http://purl.example.org/web_dev_km_bfo#"
        self.SBEKMS_NS = "http://sbekms.example.org/instances/"
    
    async def search(self, query: UnifiedSearchQuery) -> SearchResponse:
        """Unified search that automatically detects and applies appropriate search strategy"""
        start_time = time.time()
        
        try:
            # Determine search strategy
            search_mode = "advanced" if query.has_advanced_filters() else "basic"
            
            # Build appropriate SPARQL query
            if search_mode == "advanced":
                sparql_query = self._build_advanced_search_query(query)
                message_suffix = "with filters"
            else:
                sparql_query = self._build_basic_search_query(query)
                message_suffix = ""
            
            # Execute query
            query_results = await self.triplestore.query(sparql_query)
            results = query_results.get('results', {}).get('bindings', [])
            
            # Process results
            search_results = []
            for result in results:
                search_result = self._process_search_result(result, query.query)
                search_results.append(search_result)
            
            # Calculate search time
            search_time = (time.time() - start_time) * 1000
            
            # Generate suggestions for basic searches
            suggestions = []
            if search_mode == "basic":
                suggestions = await self._generate_suggestions(query.query)
            
            return SearchResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Found {len(search_results)} results {message_suffix}".strip(),
                results=search_results,
                total_results=len(search_results),
                search_time_ms=search_time,
                suggestions=suggestions,
                data={
                    "search_mode": search_mode,
                    "search_type": query.search_type,
                    "filters_applied": query.has_advanced_filters()
                }
            )
            
        except Exception as e:
            logger.error(f"Unified search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    def _build_basic_search_query(self, query: UnifiedSearchQuery) -> str:
        """Build SPARQL query for basic search"""
        if query.search_type == "semantic":
            return self._build_semantic_search_query(query.query, query.limit, query.offset)
        elif query.search_type == "textual":
            return self._build_textual_search_query(query.query, query.limit, query.offset)
        else:  # hybrid
            return self._build_semantic_search_query(query.query, query.limit, query.offset)
    
    def _build_semantic_search_query(self, query_text: str, limit: int, offset: int) -> str:
        """Build SPARQL query for semantic search"""
        return f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT DISTINCT ?asset ?fileName ?title ?description ?fileSize ?mimeType ?author ?created ?type ?tag
        WHERE {{
            ?asset a wdo:DigitalInformationCarrier .
            ?asset rdfs:label ?fileName .
            
            OPTIONAL {{ ?asset rdf:type ?type }}
            OPTIONAL {{ ?asset dcterms:title ?title }}
            OPTIONAL {{ ?asset dcterms:description ?description }}
            OPTIONAL {{ ?asset wdo:hasFileSize ?fileSize }}
            OPTIONAL {{ ?asset wdo:hasMimeType ?mimeType }}
            OPTIONAL {{ ?asset dcterms:creator ?author }}
            OPTIONAL {{ ?asset dcterms:created ?created }}
            OPTIONAL {{ ?asset wdo:hasTag ?tagURI . ?tagURI rdfs:label ?tag }}
            
            # More flexible text matching across multiple fields
            FILTER (
                CONTAINS(LCASE(?fileName), LCASE("{query_text}")) ||
                (BOUND(?title) && CONTAINS(LCASE(STR(?title)), LCASE("{query_text}"))) ||
                (BOUND(?description) && CONTAINS(LCASE(STR(?description)), LCASE("{query_text}"))) ||
                (BOUND(?tag) && CONTAINS(LCASE(STR(?tag)), LCASE("{query_text}"))) ||
                (BOUND(?type) && CONTAINS(LCASE(STR(?type)), LCASE("{query_text}"))) ||
                (BOUND(?mimeType) && CONTAINS(LCASE(STR(?mimeType)), LCASE("{query_text}")))
            )
        }}
        ORDER BY DESC(
            (IF(CONTAINS(LCASE(?fileName), LCASE("{query_text}")), 4, 0)) +
            (IF(BOUND(?title) && CONTAINS(LCASE(STR(?title)), LCASE("{query_text}")), 3, 0)) +
            (IF(BOUND(?description) && CONTAINS(LCASE(STR(?description)), LCASE("{query_text}")), 2, 0)) +
            (IF(BOUND(?tag) && CONTAINS(LCASE(STR(?tag)), LCASE("{query_text}")), 1, 0))
        ) ?fileName
        LIMIT {limit} OFFSET {offset}
        """
    
    def _build_textual_search_query(self, query_text: str, limit: int, offset: int) -> str:
        """Build SPARQL query for textual search"""
        return f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT DISTINCT ?asset ?fileName ?title ?description ?fileSize ?mimeType ?author ?created ?type ?tag
        WHERE {{
            ?asset a wdo:DigitalInformationCarrier .
            ?asset rdfs:label ?fileName .
            
            OPTIONAL {{ ?asset rdf:type ?type }}
            OPTIONAL {{ ?asset dcterms:title ?title }}
            OPTIONAL {{ ?asset dcterms:description ?description }}
            OPTIONAL {{ ?asset wdo:hasFileSize ?fileSize }}
            OPTIONAL {{ ?asset wdo:hasMimeType ?mimeType }}
            OPTIONAL {{ ?asset dcterms:creator ?author }}
            OPTIONAL {{ ?asset dcterms:created ?created }}
            OPTIONAL {{ ?asset wdo:hasTag ?tagURI . ?tagURI rdfs:label ?tag }}
            
            # Simple text matching with proper bounds checking
            FILTER (
                CONTAINS(LCASE(?fileName), LCASE("{query_text}")) ||
                (BOUND(?title) && CONTAINS(LCASE(STR(?title)), LCASE("{query_text}"))) ||
                (BOUND(?description) && CONTAINS(LCASE(STR(?description)), LCASE("{query_text}")))
            )
        }}
        ORDER BY ?fileName
        LIMIT {limit} OFFSET {offset}
        """
    
    def _build_advanced_search_query(self, query: UnifiedSearchQuery) -> str:
        """Build advanced SPARQL query with all filters"""
        base_query = f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT DISTINCT ?asset ?fileName ?title ?description ?fileSize ?mimeType ?author ?created ?type ?tag
        WHERE {{
            ?asset a wdo:DigitalInformationCarrier .
            ?asset rdfs:label ?fileName .
            ?asset rdf:type ?type .
            
            OPTIONAL {{ ?asset dcterms:title ?title }}
            OPTIONAL {{ ?asset dcterms:description ?description }}
            OPTIONAL {{ ?asset wdo:hasFileSize ?fileSize }}
            OPTIONAL {{ ?asset wdo:hasMimeType ?mimeType }}
            OPTIONAL {{ ?asset dcterms:creator ?author }}
            OPTIONAL {{ ?asset dcterms:created ?created }}
            OPTIONAL {{ ?asset wdo:hasTag ?tagURI . ?tagURI rdfs:label ?tag }}
        """
        
        # Build filters
        filters = []
        
        # Text search filter
        if query.query:
            if query.search_type == "semantic":
                filters.append(f"""
                    (CONTAINS(LCASE(?fileName), LCASE("{query.query}")) ||
                     CONTAINS(LCASE(STR(?title)), LCASE("{query.query}")) ||
                     CONTAINS(LCASE(STR(?description)), LCASE("{query.query}")) ||
                     CONTAINS(LCASE(STR(?tag)), LCASE("{query.query}")))
                """)
            else:  # textual or hybrid
                filters.append(f"""
                    (CONTAINS(LCASE(?fileName), LCASE("{query.query}")) ||
                     CONTAINS(LCASE(STR(?title)), LCASE("{query.query}")) ||
                     CONTAINS(LCASE(STR(?description)), LCASE("{query.query}")))
                """)
        
        # WDO classes filter
        if query.wdo_classes:
            wdo_filter = " || ".join([f"?type = wdo:{cls}" for cls in query.wdo_classes])
            filters.append(f"({wdo_filter})")
        
        # File types filter
        if query.file_types:
            file_type_filters = []
            for file_type in query.file_types:
                file_type_filters.append(f'REGEX(?fileName, "\\.{file_type}$", "i")')
            filters.append(f"({' || '.join(file_type_filters)})")
        
        # Author filter
        if query.author:
            filters.append(f'CONTAINS(LCASE(STR(?author)), LCASE("{query.author}"))')
        
        # File size filters
        if query.min_file_size:
            filters.append(f"?fileSize >= {query.min_file_size}")
        if query.max_file_size:
            filters.append(f"?fileSize <= {query.max_file_size}")
        
        # Date filters
        if query.date_from:
            filters.append(f'?created >= "{query.date_from}T00:00:00"^^xsd:dateTime')
        if query.date_to:
            filters.append(f'?created <= "{query.date_to}T23:59:59"^^xsd:dateTime')
        
        # Tags filter
        if query.tags:
            tag_filters = []
            for tag in query.tags:
                tag_filters.append(f'CONTAINS(LCASE(STR(?tag)), LCASE("{tag}"))')
            filters.append(f"({' || '.join(tag_filters)})")
        
        # Add all filters to query
        if filters:
            base_query += "\n            FILTER (" + " && ".join(filters) + ")"
        
        # Add ordering and pagination
        if query.query and query.search_type == "semantic":
            base_query += f"""
        }}
        ORDER BY DESC(
            (IF(CONTAINS(LCASE(?fileName), LCASE("{query.query}")), 4, 0)) +
            (IF(CONTAINS(LCASE(STR(?title)), LCASE("{query.query}")), 3, 0)) +
            (IF(CONTAINS(LCASE(STR(?description)), LCASE("{query.query}")), 2, 0))
        ) ?fileName
        LIMIT {query.limit} OFFSET {query.offset}
        """
        else:
            base_query += f"""
        }}
        ORDER BY ?fileName
        LIMIT {query.limit} OFFSET {query.offset}
        """
        
        return base_query
    
    def _process_search_result(self, result: dict, query_text: str) -> SearchResult:
        """Process SPARQL result into SearchResult model"""
        # Calculate relevance score
        relevance_score = self._calculate_relevance(result, query_text)
        
        # Extract highlights
        highlights = self._extract_highlights(result, query_text)
        
        # Extract asset ID from URI
        asset_uri = result.get('asset', {}).get('value', '')
        asset_id = asset_uri.split('/')[-1] if asset_uri else 'unknown'
        
        # Extract tags (may be multiple)
        tags = []
        if result.get('tag'):
            tag_value = result['tag']['value']
            if tag_value:
                tags.append(tag_value)
        
        # Parse creation date
        created_str = result.get('created', {}).get('value', '2024-01-01T00:00:00')
        try:
            if 'T' in created_str:
                created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            else:
                created_at = datetime.fromisoformat(f"{created_str}T00:00:00")
        except:
            created_at = datetime(2024, 1, 1)
        
        return SearchResult(
            asset_id=asset_id,
            file_name=result.get('fileName', {}).get('value', ''),
            title=result.get('title', {}).get('value') if result.get('title') else None,
            description=result.get('description', {}).get('value') if result.get('description') else None,
            file_type=self._extract_file_type(result.get('fileName', {}).get('value', '')),
            mime_type=result.get('mimeType', {}).get('value', ''),
            file_size=int(result.get('fileSize', {}).get('value', 0)),
            author=result.get('author', {}).get('value') if result.get('author') else None,
            tags=tags,
            wdo_classes=[self._extract_class_name(result.get('type', {}).get('value', ''))],
            created_at=created_at,
            relevance_score=relevance_score,
            highlights=highlights
        )
    
    def _calculate_relevance(self, result: dict, query_text: str) -> float:
        """Calculate relevance score for search result"""
        score = 0.0
        query_lower = query_text.lower()
        
        # File name matching (highest weight)
        file_name = result.get('fileName', {}).get('value', '').lower()
        if query_lower in file_name:
            score += 0.4
            if file_name.startswith(query_lower):
                score += 0.1  # Bonus for prefix match
        
        # Title matching
        title = result.get('title', {}).get('value', '')
        if title and query_lower in title.lower():
            score += 0.3
        
        # Description matching
        description = result.get('description', {}).get('value', '')
        if description and query_lower in description.lower():
            score += 0.2
        
        # Tag matching
        tag = result.get('tag', {}).get('value', '')
        if tag and query_lower in tag.lower():
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_highlights(self, result: dict, query_text: str) -> List[str]:
        """Extract highlighted text snippets"""
        highlights = []
        query_lower = query_text.lower()
        
        # Check file name
        file_name = result.get('fileName', {}).get('value', '')
        if query_lower in file_name.lower():
            highlights.append(f"📄 {file_name}")
        
        # Check title
        title = result.get('title', {}).get('value', '')
        if title and query_lower in title.lower():
            highlights.append(f"📋 {title}")
        
        # Check description with context
        description = result.get('description', {}).get('value', '')
        if description and query_lower in description.lower():
            start = max(0, description.lower().find(query_lower) - 30)
            end = min(len(description), start + 100)
            snippet = description[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(description):
                snippet = snippet + "..."
            highlights.append(f"📝 {snippet}")
        
        # Check tags
        tag = result.get('tag', {}).get('value', '')
        if tag and query_lower in tag.lower():
            highlights.append(f"🏷️ {tag}")
        
        return highlights
    
    def _extract_file_type(self, file_name: str) -> str:
        """Extract file type from file name"""
        if '.' in file_name:
            return file_name.split('.')[-1].lower()
        return 'unknown'
    
    def _extract_class_name(self, class_uri: str) -> str:
        """Extract class name from URI"""
        if '#' in class_uri:
            return class_uri.split('#')[-1]
        elif '/' in class_uri:
            return class_uri.split('/')[-1]
        return class_uri
    
    async def _generate_suggestions(self, query_text: str) -> List[str]:
        """Generate search suggestions based on existing data"""
        suggestions = []
        
        try:
            # Query for similar terms
            sparql_query = f"""
            PREFIX wdo: <{self.WDO_NS}>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            
            SELECT DISTINCT ?label
            WHERE {{
                {{
                    ?asset rdfs:label ?label .
                    FILTER CONTAINS(LCASE(?label), LCASE("{query_text[:3]}"))
                }} UNION {{
                    ?asset dcterms:title ?label .
                    FILTER CONTAINS(LCASE(STR(?label)), LCASE("{query_text[:3]}"))
                }} UNION {{
                    ?asset wdo:hasTag ?tagURI .
                    ?tagURI rdfs:label ?label .
                    FILTER CONTAINS(LCASE(?label), LCASE("{query_text[:3]}"))
                }}
            }}
            LIMIT 5
            """
            
            query_results = await self.triplestore.query(sparql_query)
            results = query_results.get('results', {}).get('bindings', [])
            for result in results:
                label = result.get('label', {}).get('value', '')
                if label and label.lower() != query_text.lower():
                    suggestions.append(label)
        
        except Exception as e:
            logger.warning(f"Failed to generate suggestions: {e}")
        
        return list(set(suggestions))[:5]  # Remove duplicates and limit


# API Endpoints
@router.get("/health")
async def search_health():
    """Search API health check"""
    return {
        "status": "healthy", 
        "service": "search", 
        "version": "2.0.0",
        "features": ["unified_search", "semantic_search", "advanced_filters", "suggestions"]
    }

@router.post("/", response_model=SearchResponse)
async def unified_search(
    query: UnifiedSearchQuery,
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """
    Unified search endpoint that automatically handles both basic and advanced search.
    
    - **Basic Search**: Just provide a query string
    - **Advanced Search**: Add any filters (file_types, wdo_classes, author, etc.)
    - **Semantic Search**: Set search_type to 'semantic' for ontology-aware search
    - **Textual Search**: Set search_type to 'textual' for simple text matching
    - **Hybrid Search**: Default mode that combines semantic and textual approaches
    """
    search_service = UnifiedSearchService(triplestore, ontology)
    return await search_service.search(query)

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions"),
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """Get search suggestions based on partial query"""
    search_service = UnifiedSearchService(triplestore, ontology)
    suggestions = await search_service._generate_suggestions(q)
    
    return SuccessResponse(
        message=f"Found {len(suggestions)} suggestions",
        data={"suggestions": suggestions[:limit]}
    )

@router.get("/facets")
async def get_search_facets(
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """Get available search facets (file types, authors, tags, etc.)"""
    try:
        # Query for available facets
        facets_query = f"""
        PREFIX wdo: <http://purl.example.org/web_dev_km_bfo#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?type ?author ?mimeType ?tag
        WHERE {{
            ?asset a wdo:DigitalInformationCarrier .
            OPTIONAL {{ ?asset rdf:type ?type }}
            OPTIONAL {{ ?asset dcterms:creator ?author }}
            OPTIONAL {{ ?asset wdo:hasMimeType ?mimeType }}
            OPTIONAL {{ ?asset wdo:hasTag ?tagURI . ?tagURI rdfs:label ?tag }}
        }}
        """
        
        query_results = await triplestore.query(facets_query)
        results = query_results.get('results', {}).get('bindings', [])
        
        # Process facets
        wdo_classes = set()
        authors = set()
        mime_types = set()
        tags = set()
        
        for result in results:
            if result.get('type'):
                class_name = result['type']['value'].split('#')[-1] if '#' in result['type']['value'] else result['type']['value'].split('/')[-1]
                if class_name != "DigitalInformationCarrier":  # Exclude base class
                    wdo_classes.add(class_name)
            
            if result.get('author'):
                authors.add(result['author']['value'])
            
            if result.get('mimeType'):
                mime_types.add(result['mimeType']['value'])
            
            if result.get('tag'):
                tags.add(result['tag']['value'])
        
        return SuccessResponse(
            message="Retrieved search facets",
            data={
                "wdo_classes": sorted(list(wdo_classes)),
                "authors": sorted(list(authors)),
                "mime_types": sorted(list(mime_types)),
                "tags": sorted(list(tags)),
                "file_types": ["py", "md", "json", "txt", "yml", "yaml", "js", "ts", "html", "css", "xml", "sql"],
                "search_types": ["semantic", "textual", "hybrid"]
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get search facets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search facets: {str(e)}") 