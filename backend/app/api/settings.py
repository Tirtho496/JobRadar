from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.core.profile import get_locations, get_profile, get_sources_config

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_api_key)])


@router.get("/profile")
async def profile() -> dict:
    candidate = get_profile()
    locations = get_locations()
    sources = get_sources_config()
    return {
        "candidate": candidate.model_dump(),
        "locations": locations.model_dump(),
        "sources": sources,
    }
