from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def assets_health():
    """Assets API health check"""
    return {"status": "healthy", "service": "assets"} 