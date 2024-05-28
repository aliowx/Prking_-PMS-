from fastapi import APIRouter

from .api.camera import router as camera_router
from .api.parkinglot import router as parkinglot_router

router = APIRouter()
router.include_router(parkinglot_router, prefix="/parking", tags=["parking"])
router.include_router(camera_router, prefix="/camera", tags=["camera"])
