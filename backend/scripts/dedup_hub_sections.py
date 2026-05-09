"""Remove duplicate hub sections (same topic_id + sort_order)."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


async def dedup():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.snugprism

    topics = await db.topics.find({}).to_list(None)
    for topic in topics:
        tid = topic["_id"]
        sections = await db.hub_sections.find({"topic_id": tid}).sort("sort_order", 1).to_list(None)
        if not sections:
            continue

        seen = set()
        to_delete = []
        for s in sections:
            key = s["sort_order"]
            if key in seen:
                to_delete.append(s["_id"])
            else:
                seen.add(key)

        if to_delete:
            result = await db.hub_sections.delete_many({"_id": {"$in": to_delete}})
            print(f"Topic {topic.get('slug')}: deleted {result.deleted_count} duplicates")

        remaining = await db.hub_sections.count_documents({"topic_id": tid})
        print(f"Topic {topic.get('slug')}: {remaining} sections remaining")

    client.close()


asyncio.run(dedup())
