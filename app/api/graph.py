from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def graph_health():
    """Graph API health check"""
    return {"status": "healthy", "service": "knowledge-graph"} 