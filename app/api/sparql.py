from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def sparql_health():
    """SPARQL API health check"""
    return {"status": "healthy", "service": "sparql"} 