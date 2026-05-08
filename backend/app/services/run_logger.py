"""Log every LLM / embedding call with token counts and cost to MongoDB."""
from __future__ import annotations
from datetime import datetime, UTC
from loguru import logger as _logger

# USD per 1M tokens (input, output). Kept here as single source of truth.
PRICING: dict[str, dict[str, float]] = {
    "gpt-4o":               {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":          {"input": 0.15,  "output": 0.60},
    "gpt-4.1":              {"input": 2.00,  "output": 8.00},
    "gpt-4.1-mini":         {"input": 0.40,  "output": 1.60},
    "gpt-4.1-nano":         {"input": 0.10,  "output": 0.40},
    "codex-mini-latest":    {"input": 1.50,  "output": 6.00},
    "codex-cli":            {"input": 1.10,  "output": 4.40},  # Codex CLI uses o4-mini internally
    "o4-mini":              {"input": 1.10,  "output": 4.40},
    "o3":                   {"input": 10.00, "output": 40.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.00},
    "text-embedding-3-large": {"input": 0.13, "output": 0.00},
}


def calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, {"input": 0.0, "output": 0.0})
    return round((input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000, 8)


async def log_run(
    call_type: str,      # "llm" | "embedding"
    model: str,
    purpose: str,        # "chat" | "qa_generation" | "topic_detection" | "embedding" | "hub_generation"
    input_tokens: int,
    output_tokens: int = 0,
) -> None:
    cost = calc_cost(model, input_tokens, output_tokens)
    try:
        from app.services.document_db import get_db
        await get_db().run_log.insert_one(
            {
                "timestamp": datetime.now(UTC),
                "call_type": call_type,
                "model": model,
                "purpose": purpose,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            }
        )
    except Exception as e:
        _logger.warning(f"run_logger: failed to persist log entry: {e}")
