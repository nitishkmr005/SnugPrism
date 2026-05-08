from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, ChatResponse
from app.services import rag
from app.services.document_db import fetch_session_messages
from config.settings import get_settings

router = APIRouter()


def _check_api_key(x_api_key: str | None) -> None:
    """Optional API key check for voice agent calls. No-ops if key not configured."""
    s = get_settings()
    if s.voice_agent_api_key and x_api_key != s.voice_agent_api_key:
        raise HTTPException(401, "Invalid API key")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    x_api_key: str | None = Header(default=None),
):
    _check_api_key(x_api_key)

    if body.stream:
        return StreamingResponse(
            rag.chat_stream(
                body.message,
                body.session_id,
                body.include_web_search,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    result = await rag.chat(
        body.message,
        body.session_id,
        body.include_web_search,
        body.format,
    )
    return ChatResponse(**result)


@router.get("/chat/sessions/{session_id}/history")
async def get_history(session_id: str):
    messages = await fetch_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}
