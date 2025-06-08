from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def ontology_health():
    """Ontology API health check"""
    return {"status": "healthy", "service": "ontology"} 