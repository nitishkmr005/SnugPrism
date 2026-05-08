from fastapi import APIRouter, HTTPException, Query
from app.models import QuestionOut, QuestionCreate, QuestionUpdate, QuestionsPage
from app.services.document_db import (
    fetch_questions,
    fetch_question_by_id,
    insert_question,
    update_question,
    delete_question,
)

router = APIRouter()


def _to_out(row: dict) -> QuestionOut:
    ct = row.get("comparison_table")
    return QuestionOut(
        id=row["id"],
        topic=row["topic"],
        question=row["question"],
        answer=row["answer"],
        difficulty=row["difficulty"],
        tags=row.get("tags") or [],
        code_snippet=row.get("code_snippet"),
        comparison_table=ct,
        reference_urls=row.get("reference_urls") or [],
        pdf_links=row.get("pdf_links") or [],
        source=row.get("source", "manual"),
        created_at=row["created_at"],
    )


@router.get("/questions", response_model=QuestionsPage)
async def list_questions(
    topic_slug: str | None = Query(None),
    difficulty: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = await fetch_questions(topic_slug, difficulty, q, limit, offset)
    return QuestionsPage(items=[_to_out(r) for r in items], total=total)


@router.get("/questions/{qid}", response_model=QuestionOut)
async def get_question(qid: str):
    row = await fetch_question_by_id(qid)
    if not row:
        raise HTTPException(404, "Question not found")
    return _to_out(row)


@router.post("/questions", response_model=QuestionOut, status_code=201)
async def create_question(body: QuestionCreate):
    row = await insert_question(body.model_dump(exclude_none=True))
    return _to_out(row)


@router.put("/questions/{qid}", response_model=QuestionOut)
async def edit_question(qid: str, body: QuestionUpdate):
    if not await fetch_question_by_id(qid):
        raise HTTPException(404, "Question not found")
    row = await update_question(qid, body.model_dump(exclude_none=True))
    return _to_out(row)


@router.delete("/questions/{qid}")
async def remove_question(qid: str):
    if not await fetch_question_by_id(qid):
        raise HTTPException(404, "Question not found")
    await delete_question(qid)
    return {"deleted": qid}
