"""MongoDB async client (Motor). All structured data access goes through here."""
from __future__ import annotations
from datetime import datetime, UTC
import re
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


def _question_key(question: str) -> str:
    """Normalize question text so near-identical duplicates collapse to one row."""
    return " ".join(question.strip().lower().split())


async def init_indexes() -> None:
    """Ensure required indexes exist (idempotent)."""
    db = get_db()
    await db.questions.create_index([("question", "text")], name="question_text", background=True)
    await db.topics.create_index("slug", unique=True, background=True)
    await db.documents.create_index(
        [("source_type", 1), ("source_ref", 1)],
        unique=True,
        name="document_source_unique",
        background=True,
    )
    await db.questions.create_index(
        [("topic_id", 1), ("question_key", 1)],
        unique=True,
        name="question_unique_per_topic",
        background=True,
    )
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
    tag: str | None = None,
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

    if tag:
        match["tags"] = tag

    dedupe_pipeline = [
        {"$match": match},
        {"$sort": {"created_at": 1}},
        {
            "$addFields": {
                "_normalized_question": {
                    "$ifNull": [
                        "$question_key",
                        {
                            "$trim": {"input": {"$toLower": "$question"}}
                        },
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "topic_id": "$topic_id",
                    "question": "$_normalized_question",
                },
                "doc": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$doc"}},
        {"$project": {"_normalized_question": 0}},
    ]

    total_cursor = db.questions.aggregate([
        *dedupe_pipeline,
        {"$count": "total"},
    ])
    total = 0
    async for row in total_cursor:
        total = row["total"]
        break

    pipeline = [
        *dedupe_pipeline,
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
    p["question_key"] = _question_key(p["question"])
    p.setdefault("created_at", datetime.now(UTC))
    result = await get_db().questions.insert_one(p)
    return await fetch_question_by_id(str(result.inserted_id))


async def update_question(qid: str, payload: dict) -> dict:
    p = dict(payload)
    if "topic_id" in p and isinstance(p["topic_id"], str):
        p["topic_id"] = ObjectId(p["topic_id"])
    if "question" in p:
        p["question_key"] = _question_key(p["question"])
    await get_db().questions.update_one({"_id": ObjectId(qid)}, {"$set": p})
    return await fetch_question_by_id(qid)


async def delete_question(qid: str) -> None:
    await get_db().questions.delete_one({"_id": ObjectId(qid)})


async def delete_generated_questions_for_document(title: str, source_ref: str | None = None) -> int:
    """Delete generated Q&A rows previously cited to the same document/source."""
    answer_matches = [{"answer": {"$regex": re.escape(title)}}]
    if source_ref and source_ref != title:
        answer_matches.append({"answer": {"$regex": re.escape(source_ref)}})
    matches = answer_matches + ([{"reference_urls": source_ref}] if source_ref else [])
    result = await get_db().questions.delete_many(
        {
            "source": "generated",
            "$or": matches,
        }
    )
    return result.deleted_count


async def cleanup_duplicate_questions() -> int:
    """Keep the oldest Q&A for each topic/question pair across all sources."""
    db = get_db()
    pipeline = [
        {
            "$addFields": {
                "_normalized_question": {
                    "$ifNull": [
                        "$question_key",
                        {
                            "$trim": {"input": {"$toLower": "$question"}}
                        },
                    ]
                }
            }
        },
        {"$sort": {"created_at": 1, "_id": 1}},
        {
            "$group": {
                "_id": {"topic_id": "$topic_id", "question": "$_normalized_question"},
                "ids": {"$push": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    stale_ids = []
    async for group in db.questions.aggregate(pipeline):
        stale_ids.extend(group["ids"][1:])
    if stale_ids:
        await db.questions.delete_many({"_id": {"$in": stale_ids}})
    await db.questions.update_many(
        {"$or": [{"question_key": {"$exists": False}}, {"question_key": ""}]},
        [{"$set": {"question_key": {"$trim": {"input": {"$toLower": "$question"}}}}}],
    )
    return len(stale_ids)


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


async def cleanup_duplicate_documents() -> list[str]:
    """
    Remove duplicate document rows before creating the unique source index.

    Keeps the row with the most indexed chunks, then the newest ingest time.
    Returns deleted document ids so callers can remove orphaned vector points.
    """
    db = get_db()
    pipeline = [
        {
            "$group": {
                "_id": {"source_type": "$source_type", "source_ref": "$source_ref"},
                "count": {"$sum": 1},
                "docs": {
                    "$push": {
                        "_id": "$_id",
                        "chunk_count": "$chunk_count",
                        "ingested_at": "$ingested_at",
                    }
                },
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]

    deleted_ids: list[str] = []
    async for group in db.documents.aggregate(pipeline):
        docs = sorted(
            group["docs"],
            key=lambda d: (d.get("chunk_count") or 0, d.get("ingested_at") or datetime.min.replace(tzinfo=UTC)),
            reverse=True,
        )
        stale_ids = [d["_id"] for d in docs[1:]]
        if stale_ids:
            await db.documents.delete_many({"_id": {"$in": stale_ids}})
            deleted_ids.extend(str(oid) for oid in stale_ids)
    return deleted_ids


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


async def fetch_document_by_id(doc_id: str) -> dict | None:
    try:
        doc = await get_db().documents.find_one({"_id": ObjectId(doc_id)})
    except Exception:
        return None
    return _doc(doc)


async def fetch_document_by_source_ref(source_ref: str) -> dict | None:
    doc = await get_db().documents.find_one({"source_ref": source_ref})
    return _doc(doc)


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
    cursor = get_db().hub_sections.find({"topic_id": ObjectId(topic_id)}).sort("sort_order", 1)
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
