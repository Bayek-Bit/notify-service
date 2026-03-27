from fastapi import APIRouter, Depends
from .auth.dependencies import verify_service_token

router = APIRouter()


@router.get("/protected", dependencies=[Depends(verify_service_token)])
async def protected_route():
    return {"message": "data"}
