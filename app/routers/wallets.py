from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def wallet_health():
    """Health check endpoint for wallet service"""
    return {"status": "ok"}

