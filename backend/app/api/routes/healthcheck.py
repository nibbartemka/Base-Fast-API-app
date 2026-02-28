from fastapi import APIRouter, status


router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_healthcheck():
    return {
        "status": "ok"
    }

