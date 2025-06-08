from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def search_health():
    """Search API health check"""
    return {"status": "healthy", "service": "search"} 