"""Run OpenAI Codex CLI in non-interactive mode for headless tasks.

Uses `codex exec --json` which outputs JSONL; we parse agent_message events
for the response text and turn.completed for token usage.
"""
from __future__ import annotations
import asyncio
import json
import os
from loguru import logger
from config.settings import get_settings

_MODEL = "codex-cli"


async def run(prompt: str, purpose: str = "qa_generation") -> str:
    """Execute prompt via `codex exec --json` non-interactively.

    Raises RuntimeError if codex is not installed or the run fails.
    Falls back gracefully — callers should catch RuntimeError and use llm.complete().
    """
    s = get_settings()
    env = {
        **os.environ,
        "CODEX_API_KEY": s.openai_api_key,
        "OPENAI_API_KEY": s.openai_api_key,
    }
    proc = await asyncio.create_subprocess_exec(
        "codex", "exec",
        "--ephemeral",
        "--sandbox", "workspace-write",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--json",
        prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        cwd="/tmp",
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"codex exec failed (rc={proc.returncode}): {stderr.decode()[:400]}"
        )

    response_text = ""
    input_tokens = 0
    output_tokens = 0

    for line in stdout.decode().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            etype = event.get("type", "")
            if etype == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    response_text = item.get("text", "")
            elif etype == "turn.completed":
                usage = event.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
        except json.JSONDecodeError:
            pass

    if input_tokens or output_tokens:
        from app.services.run_logger import log_run
        await log_run("llm", _MODEL, purpose, input_tokens, output_tokens)
        logger.info(f"Codex [{purpose}]: in={input_tokens} out={output_tokens} tokens")

    logger.info(f"Codex exec completed ({len(response_text)} chars)")
    return response_text
