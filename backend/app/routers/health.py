from fastapi import APIRouter
from app.services.document_db import get_db
from app.services.vector_db import get_client as get_qdrant
from config.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    s = get_settings()

    try:
        await get_db().command("ping")
        mongo_status = "connected"
    except Exception:
        mongo_status = "unavailable"

    try:
        await get_qdrant().get_collections()
        qdrant_status = "connected"
    except Exception:
        qdrant_status = "unavailable"

    return {
        "status": "ok",
        "version": s.app_version,
        "mongodb": mongo_status,
        "qdrant": qdrant_status,
    }
