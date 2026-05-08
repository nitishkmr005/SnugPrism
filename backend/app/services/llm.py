"""Provider-agnostic LLM layer. Only this file knows about OpenAI/Anthropic."""
from __future__ import annotations
from typing import AsyncGenerator
from loguru import logger
from config.settings import get_settings


async def complete(
    messages: list[dict],
    max_tokens: int | None = None,
    model: str | None = None,
    purpose: str = "chat",
) -> str:
    """Return a full string response. model overrides settings.openai_model."""
    s = get_settings()
    mt = max_tokens or s.llm_max_tokens
    use_model = model or s.openai_model
    if s.llm_provider == "openai":
        return await _complete_openai(messages, mt, use_model, purpose)
    raise ValueError(f"Unsupported llm_provider: {s.llm_provider}")


async def stream(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Yield token strings from the configured LLM provider."""
    s = get_settings()
    if s.llm_provider == "openai":
        async for token in _stream_openai(messages, s.openai_model):
            yield token
        return
    raise ValueError(f"Unsupported llm_provider: {s.llm_provider}")


async def _complete_openai(messages: list[dict], max_tokens: int, model: str, purpose: str) -> str:
    from openai import AsyncOpenAI
    from app.services.run_logger import log_run
    s = get_settings()
    client = AsyncOpenAI(api_key=s.openai_api_key)
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    text = resp.choices[0].message.content or ""
    if resp.usage:
        await log_run("llm", model, purpose, resp.usage.prompt_tokens, resp.usage.completion_tokens)
        logger.debug(f"LLM [{model}] {purpose}: {resp.usage.total_tokens} tokens")
    return text


async def _stream_openai(messages: list[dict], model: str) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI
    from app.services.run_logger import log_run
    s = get_settings()
    client = AsyncOpenAI(api_key=s.openai_api_key)
    stream_resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        stream=True,
        stream_options={"include_usage": True},
    )
    async for chunk in stream_resp:
        if chunk.usage:
            await log_run("llm", model, "chat", chunk.usage.prompt_tokens, chunk.usage.completion_tokens)
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
