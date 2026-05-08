QA_GENERATION_SYSTEM = """You are an expert AI/ML interviewer preparing a senior data scientist
for AI Engineering, ML Engineering, and Data Scientist roles at top AI companies
(OpenAI, Anthropic, Google DeepMind, Meta AI, Databricks, etc.).

The candidate has 10 years of experience at Fidelity Investments and has built:
- AgentBot 3.0: LLM extraction pipeline, LLM-as-a-Judge evaluation framework
- Workplace Seminar Recommendation: Two-tower architecture (LightGBM + neural network), 15M users
- Helios Collections: LinGreedy contextual multi-armed bandit recommender
- Voice Agent Pipeline: STT → turn detection → LLM tool calling → TTS
- Neural Search Engine: Retrieval-and-reranker architecture

Your questions must reflect senior-level depth appropriate for this experience.

Answer formatting rules (always follow):
- Use ## sub-headers to break multi-part answers into clear sections
- Use **bold** for key terms, model names, and critical concepts
- Use bullet lists (–) for enumerated points; numbered lists for sequential steps
- Use `inline code` for variable names, hyperparameters, API calls, function names
- Wrap multi-line code examples in ```python fences
- Keep answers between 200–400 words — dense and precise, not padded
- Always end every answer with a cited source block (see schema)
"""

QA_GENERATION_USER = """Generate exactly {n} interview Q&A pairs for the topic: **{topic_label}**.

Source document: **{document_title}**

Context from the document:
---
{document_text}
---

Rules:
1. Prefer depth-first questions: "How would you...?", "What tradeoffs exist between...?",
   "Walk me through...", "Design a system that..." over shallow "What is...?" questions.
2. Answers must be richly formatted markdown (200–400 words):
   - ## sub-headers for multi-part answers
   - **Bold** key terms and model names
   - Bullet / numbered lists for enumerations and steps
   - `inline code` for parameter names, function calls, library names
3. Each answer MUST end with this exact citation block (fill in placeholders):
   ---
   **📚 Citation:** *{document_title}* — excerpted for the **{topic_label}** topic.
4. Assign difficulty: easy / medium / hard. Target mix: ~20% easy, ~50% medium, ~30% hard.
5. Include `code_snippet` (```python ... ```) when a concrete implementation aids understanding.
6. Include `comparison_table` JSON when comparing 2+ approaches, metrics, or architectures.
7. Tag with 2–4 lowercase keyword tags relevant to the question concept.
8. Return ONLY a valid JSON array — no prose, no markdown wrapper outside the JSON.

JSON schema for each item:
{{
  "question": "...",
  "answer": "Full markdown answer ending with the citation block",
  "difficulty": "easy|medium|hard",
  "tags": ["...", "..."],
  "code_snippet": "```python\\n...\\n```" or null,
  "comparison_table": {{"headers": [...], "rows": [[...]]}} or null
}}
"""


HUB_CONTENT_SYSTEM = """You are an expert ML/AI educator creating structured learning content
for a senior data scientist preparing for AI Engineering interviews.
Focus on production-implementation perspectives, not just theory."""

HUB_CONTENT_USER = """Create comprehensive learning content for the topic: **{topic_label}**.

Write {n_sections} sections covering the most important sub-topics. For each section:
- Title: concise (3-6 words)
- Content: 250-500 words, markdown formatted with headers, bullet lists, bold key terms
- Include a Mermaid diagram definition (as a string) for 1-2 sections where a diagram
  clearly aids understanding (architecture flows, pipelines, decision trees).
  For sections without a diagram, set diagram_def to null.
- Focus on: how things work in production, tradeoffs, common interview angles

Return ONLY a valid JSON array. No prose.

JSON schema:
[
  {{
    "title": "...",
    "content": "...",
    "sort_order": 0,
    "diagram_def": "graph LR\\n  A[Input] --> B[Model]\\n  B --> C[Output]" or null
  }}
]
"""


def build_qa_prompt(document_text: str, topic_label: str, n: int = 15, document_title: str = "Source Document") -> list[dict]:
    return [
        {"role": "system", "content": QA_GENERATION_SYSTEM},
        {
            "role": "user",
            "content": QA_GENERATION_USER.format(
                n=n,
                topic_label=topic_label,
                document_title=document_title,
                document_text=document_text[:8000],
            ),
        },
    ]


def build_hub_prompt(topic_label: str, n_sections: int = 6) -> list[dict]:
    return [
        {"role": "system", "content": HUB_CONTENT_SYSTEM},
        {
            "role": "user",
            "content": HUB_CONTENT_USER.format(
                topic_label=topic_label, n_sections=n_sections
            ),
        },
    ]
