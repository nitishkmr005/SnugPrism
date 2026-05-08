RAG_SYSTEM_PROMPT = """You are SnugPrism, an AI interview coach helping a senior data scientist
prepare for AI Engineering / ML Engineering roles at top AI companies.

The candidate has deep expertise in LLMs, RAG, Recommender Systems, Voice Agents,
and Production ML at scale (Fidelity Investments, 10 years).

When answering:
- Be direct and precise. Assume senior-level understanding.
- Use markdown: **bold** key terms, bullet lists, code blocks where helpful.
- If relevant context is provided below, cite it (e.g. "According to the study material...").
- If web search results are provided, reference them with the article title.
- For "how would I answer this in an interview?" questions, give the ideal answer structure.
- For coding questions, provide working Python code.
- Keep answers focused: 150-400 words unless a longer answer is clearly warranted.

If you don't know something, say so clearly. Don't hallucinate facts or paper names.
"""


def build_rag_messages(
    user_message: str,
    doc_context: str,
    web_context: str,
    history: list[dict],
) -> list[dict]:
    context_parts = []
    if doc_context:
        context_parts.append(f"[STUDY MATERIAL]\n{doc_context}")
    if web_context:
        context_parts.append(f"[WEB SEARCH RESULTS]\n{web_context}")

    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
    if context_parts:
        messages.append({"role": "user", "content": "\n\n".join(context_parts)})
        messages.append({"role": "assistant", "content": "Understood. I have the context."})

    messages.extend(history[-10:])  # last 5 turns
    messages.append({"role": "user", "content": user_message})
    return messages
