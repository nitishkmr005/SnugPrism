from fastapi import APIRouter, HTTPException
from app.models import HubResponse, TopicOut, HubSection, DocumentOut
from app.services.document_db import fetch_topic_by_slug, fetch_hub_sections, fetch_documents_by_topic_id

router = APIRouter()


@router.get("/hub/{topic_slug}", response_model=HubResponse)
async def get_hub(topic_slug: str):
    topic = await fetch_topic_by_slug(topic_slug)
    if not topic:
        raise HTTPException(404, "Topic not found")
    sections = await fetch_hub_sections(topic["id"])
    documents = await fetch_documents_by_topic_id(topic["id"])
    return HubResponse(
        topic=TopicOut(**topic),
        sections=[HubSection(**s) for s in sections],
        documents=[DocumentOut(**d) for d in documents],
    )
