from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from pydantic import BaseModel, Field

from app.models.common import SuccessResponse
from app.core.triplestore_client import TriplestoreClient
from app.dependencies import get_triplestore_client

router = APIRouter()
logger = logging.getLogger(__name__)

class SPARQLQuery(BaseModel):
    """SPARQL query request model"""
    query: str = Field(..., min_length=1, description="SPARQL query string")
    format: str = Field("json", description="Response format (json, xml, turtle, etc.)")

@router.get("/health")
async def sparql_health():
    """SPARQL API health check"""
    return {"status": "healthy", "service": "sparql"}

@router.post("/query", response_model=SuccessResponse)
async def execute_sparql_query(
    sparql_request: SPARQLQuery,
    triplestore: TriplestoreClient = Depends(get_triplestore_client)
):
    """Execute a SPARQL query against the triplestore"""
    try:
        logger.info(f"Executing SPARQL query: {sparql_request.query[:100]}...")
        
        # Execute the query
        results = await triplestore.query(sparql_request.query)
        
        return SuccessResponse(
            message="SPARQL query executed successfully",
            data={
                "query": sparql_request.query,
                "results": results,
                "format": sparql_request.format,
                "result_count": len(results.get('results', {}).get('bindings', []))
            }
        )
        
    except Exception as e:
        logger.error(f"SPARQL query failed: {e}")
        raise HTTPException(status_code=500, detail=f"SPARQL query failed: {str(e)}")

@router.post("/update", response_model=SuccessResponse)
async def execute_sparql_update(
    sparql_request: SPARQLQuery,
    triplestore: TriplestoreClient = Depends(get_triplestore_client)
):
    """Execute a SPARQL UPDATE query against the triplestore"""
    try:
        logger.info(f"Executing SPARQL update: {sparql_request.query[:100]}...")
        
        # Execute the update
        result = await triplestore.update(sparql_request.query)
        
        return SuccessResponse(
            message="SPARQL update executed successfully",
            data={
                "query": sparql_request.query,
                "result": result,
                "format": sparql_request.format
            }
        )
        
    except Exception as e:
        logger.error(f"SPARQL update failed: {e}")
        raise HTTPException(status_code=500, detail=f"SPARQL update failed: {str(e)}")

@router.get("/examples")
async def get_sparql_examples():
    """Get example SPARQL queries for testing"""
    return SuccessResponse(
        message="SPARQL query examples",
        data={
            "examples": [
                {
                    "name": "List all assets",
                    "description": "Find all uploaded digital assets",
                    "query": """PREFIX wdo: <http://purl.example.org/web_dev_km_bfo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?asset ?fileName ?type WHERE {
    ?asset a wdo:DigitalInformationCarrier .
    ?asset rdfs:label ?fileName .
    ?asset rdf:type ?type .
} LIMIT 10"""
                },
                {
                    "name": "Find assets by filename",
                    "description": "Search for assets containing 'demo' in filename",
                    "query": """PREFIX wdo: <http://purl.example.org/web_dev_km_bfo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?asset ?fileName WHERE {
    ?asset a wdo:DigitalInformationCarrier .
    ?asset rdfs:label ?fileName .
    FILTER(CONTAINS(LCASE(?fileName), "demo"))
} LIMIT 10"""
                },
                {
                    "name": "Count all triples",
                    "description": "Count total number of triples in the database",
                    "query": "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
                },
                {
                    "name": "List all classes",
                    "description": "Find all RDF classes in the database",
                    "query": """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?class WHERE {
    ?instance rdf:type ?class .
} ORDER BY ?class"""
                },
                {
                    "name": "Find assets with tags",
                    "description": "Find assets and their semantic tags",
                    "query": """PREFIX wdo: <http://purl.example.org/web_dev_km_bfo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?asset ?fileName ?tag WHERE {
    ?asset a wdo:DigitalInformationCarrier .
    ?asset rdfs:label ?fileName .
    ?asset wdo:hasTag ?tagURI .
    ?tagURI rdfs:label ?tag .
} LIMIT 10"""
                }
            ]
        }
    ) 