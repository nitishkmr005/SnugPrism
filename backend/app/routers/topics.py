from fastapi import APIRouter
from app.models import TopicOut
from app.services.document_db import fetch_topics

router = APIRouter()


@router.get("/topics", response_model=list[TopicOut])
async def list_topics():
    return await fetch_topics()
