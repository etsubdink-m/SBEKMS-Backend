from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def users_health():
    """Users API health check"""
    return {"status": "healthy", "service": "users"} 