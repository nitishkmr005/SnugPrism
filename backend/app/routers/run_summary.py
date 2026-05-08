from fastapi import APIRouter
from app.services.document_db import fetch_run_logs
from app.services.run_logger import PRICING

router = APIRouter()


@router.get("/run-summary")
async def get_run_summary():
    entries = await fetch_run_logs(limit=1000)

    total_cost = sum(e["cost_usd"] for e in entries)
    total_input = sum(e["input_tokens"] for e in entries)
    total_output = sum(e["output_tokens"] for e in entries)

    by_model: dict[str, dict] = {}
    by_purpose: dict[str, dict] = {}

    for e in entries:
        m = e["model"]
        by_model.setdefault(m, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        by_model[m]["calls"] += 1
        by_model[m]["input_tokens"] += e["input_tokens"]
        by_model[m]["output_tokens"] += e["output_tokens"]
        by_model[m]["cost_usd"] = round(by_model[m]["cost_usd"] + e["cost_usd"], 8)

        p = e["purpose"]
        by_purpose.setdefault(p, {"calls": 0, "cost_usd": 0.0})
        by_purpose[p]["calls"] += 1
        by_purpose[p]["cost_usd"] = round(by_purpose[p]["cost_usd"] + e["cost_usd"], 8)

    return {
        "total_cost_usd": round(total_cost, 6),
        "total_calls": len(entries),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "by_model": by_model,
        "by_purpose": by_purpose,
        "entries": entries,
        "pricing": PRICING,
    }
