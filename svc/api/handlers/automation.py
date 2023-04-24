from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from svc.services.infrastructure.healthcheck_manager import HealthcheckManager

router = APIRouter(prefix="")


@router.get("/health")
async def health(healthcheck_manager: HealthcheckManager = Depends(HealthcheckManager)) -> JSONResponse:
    await healthcheck_manager.check_db()
    return JSONResponse(None)
