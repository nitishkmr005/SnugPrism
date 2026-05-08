# Voice Agent Integration

SnugPrism exposes a REST API for the voice agent (separate repo) to call.

## Chat Endpoint

```http
POST https://your-railway-backend.up.railway.app/api/chat
Content-Type: application/json
X-API-Key: your-voice-agent-api-key

{
  "message": "Explain the two-tower recommender architecture",
  "session_id": "voice-session-abc123",
  "stream": false,
  "include_web_search": false,
  "format": "text"
}
```

**Notes:**
- `stream: false` — returns full JSON body, no SSE parsing needed
- `format: "text"` — strips markdown formatting for clean TTS output
- `session_id` — create once at call start, pass on every turn for conversation context

**Response:**
```json
{
  "session_id": "voice-session-abc123",
  "reply": "The two-tower model separates query and document encoding into two neural networks...",
  "sources": [
    { "chunk_id": "...", "score": 0.91, "content_preview": "...", "doc_title": "..." }
  ],
  "articles": []
}
```

## Get a Practice Question

```http
GET /api/questions?topic_slug=llms&difficulty=hard&limit=1
```

Returns one random hard LLM question. The voice agent can read it aloud and wait for the user's answer.

## Session Management

```python
import httpx

BASE_URL = "https://your-railway-backend.up.railway.app"
API_KEY = "your-voice-agent-api-key"
session_id = None  # None on first call; reuse for conversation context

async def ask_coach(question: str) -> str:
    global session_id
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": question,
                "session_id": session_id,
                "stream": False,
                "include_web_search": False,
                "format": "text",
            },
            headers={"X-API-Key": API_KEY},
            timeout=30,
        )
        data = resp.json()
        session_id = data["session_id"]  # persist for next turn
        return data["reply"]
```

## Env Var

Set `VOICE_AGENT_API_KEY` in the Railway backend environment to the same value used in `X-API-Key`.
