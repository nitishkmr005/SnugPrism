"""MongoDB async client (Motor). All structured data access goes through here."""
from __future__ import annotations
from datetime import datetime, UTC
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.settings import get_settings

_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(get_settings().mongodb_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    s = get_settings()
    return _get_client()[s.mongodb_database]


def _doc(d: dict | None) -> dict | None:
    """Convert MongoDB _id (ObjectId) to str id field."""
    if d and "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


async def init_indexes() -> None:
    """Ensure required indexes exist (idempotent)."""
    db = get_db()
    await db.questions.create_index([("question", "text")], name="question_text", background=True)
    await db.topics.create_index("slug", unique=True, background=True)
    await db.hub_sections.create_index([("topic_id", 1), ("sort_order", 1)], background=True)
    await db.chat_messages.create_index([("session_id", 1), ("created_at", 1)], background=True)


# ── Topics ────────────────────────────────────────────────────────────────────

async def fetch_topics() -> list[dict]:
    cursor = get_db().topics.find().sort("sort_order", 1)
    return [_doc(t) async for t in cursor]


async def fetch_topic_by_slug(slug: str) -> dict | None:
    doc = await get_db().topics.find_one({"slug": slug})
    return _doc(doc)


async def fetch_topic_by_id(topic_id: str) -> dict | None:
    doc = await get_db().topics.find_one({"_id": ObjectId(topic_id)})
    return _doc(doc)


async def insert_topic(payload: dict) -> dict:
    result = await get_db().topics.insert_one(payload)
    doc = await get_db().topics.find_one({"_id": result.inserted_id})
    return _doc(doc)


# ── Questions ─────────────────────────────────────────────────────────────────

async def fetch_questions(
    topic_slug: str | None,
    difficulty: str | None,
    q: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    """Return (items, total_count) with topic embedded."""
    db = get_db()
    match: dict = {}

    if topic_slug:
        topic = await fetch_topic_by_slug(topic_slug)
        if not topic:
            return [], 0
        match["topic_id"] = ObjectId(topic["id"])

    if difficulty:
        match["difficulty"] = difficulty

    if q:
        match["$text"] = {"$search": q}

    total = await db.questions.count_documents(match)
    pipeline = [
        {"$match": match},
        {"$sort": {"created_at": 1}},
        {"$skip": offset},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "topics",
                "localField": "topic_id",
                "foreignField": "_id",
                "as": "_topic",
            }
        },
        {"$addFields": {"topic": {"$arrayElemAt": ["$_topic", 0]}}},
        {"$project": {"_topic": 0, "topic_id": 0}},
    ]
    cursor = db.questions.aggregate(pipeline)
    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        if doc.get("topic") and "_id" in doc["topic"]:
            doc["topic"]["id"] = str(doc["topic"].pop("_id"))
        items.append(doc)
    return items, total


async def fetch_question_by_id(qid: str) -> dict | None:
    db = get_db()
    try:
        oid = ObjectId(qid)
    except Exception:
        return None
    pipeline = [
        {"$match": {"_id": oid}},
        {
            "$lookup": {
                "from": "topics",
                "localField": "topic_id",
                "foreignField": "_id",
                "as": "_topic",
            }
        },
        {"$addFields": {"topic": {"$arrayElemAt": ["$_topic", 0]}}},
        {"$project": {"_topic": 0, "topic_id": 0}},
    ]
    cursor = db.questions.aggregate(pipeline)
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        if doc.get("topic") and "_id" in doc["topic"]:
            doc["topic"]["id"] = str(doc["topic"].pop("_id"))
        return doc
    return None


async def insert_question(payload: dict) -> dict:
    p = dict(payload)
    if "topic_id" in p and isinstance(p["topic_id"], str):
        p["topic_id"] = ObjectId(p["topic_id"])
    p.setdefault("created_at", datetime.now(UTC))
    result = await get_db().questions.insert_one(p)
    return await fetch_question_by_id(str(result.inserted_id))


async def update_question(qid: str, payload: dict) -> dict:
    p = dict(payload)
    if "topic_id" in p and isinstance(p["topic_id"], str):
        p["topic_id"] = ObjectId(p["topic_id"])
    await get_db().questions.update_one({"_id": ObjectId(qid)}, {"$set": p})
    return await fetch_question_by_id(qid)


async def delete_question(qid: str) -> None:
    await get_db().questions.delete_one({"_id": ObjectId(qid)})


# ── Documents ─────────────────────────────────────────────────────────────────

async def insert_document(title: str, source_type: str, source_ref: str, topic_ids: list[str]) -> dict:
    doc = {
        "title": title,
        "source_type": source_type,
        "source_ref": source_ref,
        "topic_ids": topic_ids,
        "chunk_count": 0,
        "ingested_at": datetime.now(UTC),
    }
    result = await get_db().documents.insert_one(doc)
    inserted = await get_db().documents.find_one({"_id": result.inserted_id})
    return _doc(inserted)


async def update_document_chunk_count(doc_id: str, chunk_count: int) -> None:
    await get_db().documents.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"chunk_count": chunk_count}},
    )


async def update_document_topic_ids(doc_id: str, topic_ids: list[str]) -> None:
    await get_db().documents.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"topic_ids": topic_ids}},
    )


async def fetch_documents() -> list[dict]:
    cursor = get_db().documents.find().sort("ingested_at", -1)
    return [_doc(d) async for d in cursor]


async def fetch_documents_by_topic_id(topic_id: str) -> list[dict]:
    """Return documents tagged with the given topic_id, newest first."""
    cursor = get_db().documents.find({"topic_ids": topic_id}).sort("ingested_at", -1)
    return [_doc(d) async for d in cursor]


# ── Chat ──────────────────────────────────────────────────────────────────────

async def create_chat_session(source: str = "web") -> dict:
    doc = {"source": source, "created_at": datetime.now(UTC)}
    result = await get_db().chat_sessions.insert_one(doc)
    return {"id": str(result.inserted_id), "source": source}


async def fetch_session_messages(session_id: str) -> list[dict]:
    cursor = get_db().chat_messages.find({"session_id": session_id}).sort("created_at", 1)
    return [_doc(m) async for m in cursor]


async def insert_chat_message(
    session_id: str, role: str, content: str, sources: list, articles: list
) -> None:
    await get_db().chat_messages.insert_one(
        {
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources,
            "articles": articles,
            "created_at": datetime.now(UTC),
        }
    )


# ── Hub ───────────────────────────────────────────────────────────────────────

async def fetch_hub_sections(topic_id: str) -> list[dict]:
    cursor = get_db().hub_sections.find({"topic_id": topic_id}).sort("sort_order", 1)
    return [_doc(s) async for s in cursor]


async def insert_hub_sections_batch(rows: list[dict]) -> None:
    if rows:
        await get_db().hub_sections.insert_many(rows)


# ── Run Log ───────────────────────────────────────────────────────────────────

async def fetch_run_logs(limit: int = 500) -> list[dict]:
    cursor = get_db().run_log.find().sort("timestamp", -1).limit(limit)
    rows = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        doc["timestamp"] = doc["timestamp"].isoformat() if hasattr(doc["timestamp"], "isoformat") else str(doc["timestamp"])
        rows.append(doc)
    return rows
