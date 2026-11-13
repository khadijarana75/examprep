"""
query_expansion.py
Unit 7 — Advanced Retrieval Strategies: multi-query retriever.
Generates a few rephrasings of one topic/question so retrieval covers
more of the document than a single embedding query would catch, then
merges + dedupes results before reranking narrows them back down.
"""

import json
import re
import time
import requests
import config


class LLMError(Exception):
    pass


def _call_groq(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
    if not config.GROQ_API_KEY:
        raise LLMError("GROQ_API_KEY is not set — add it to .env")

    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.GROQ_MODEL,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    for attempt in range(max_retries + 1):
        resp = requests.post(config.GROQ_API_URL, headers=headers, json=payload, timeout=30)

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]

        if resp.status_code == 429 and attempt < max_retries:
            wait_match = re.search(r"try again in ([\d.]+)s", resp.text)
            wait_seconds = float(wait_match.group(1)) if wait_match else (2 ** attempt)
            time.sleep(wait_seconds + 0.5)
            continue

        raise LLMError(f"Groq API error {resp.status_code}: {resp.text[:300]}")

    raise LLMError("Groq rate limit persisted after all retries.")


EXPANSION_SYSTEM_PROMPT = """You generate alternate phrasings of a topic or question \
to widen document search coverage. Given one topic, produce 2 additional rephrasings \
that approach it from different angles (a more specific angle, a more general angle, \
or a related sub-topic) while staying on the same subject.

Respond with ONLY a raw JSON array of strings, no markdown fences, no preamble:
["rephrasing 1", "rephrasing 2"]
"""


def expand_query(topic: str) -> list[str]:
    """Returns [original_topic, rephrasing_1, rephrasing_2]."""
    raw = _call_groq(EXPANSION_SYSTEM_PROMPT, topic)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
    if not match:
        raise LLMError(f"Could not find JSON array in response: {raw[:200]}")

    rephrasings = json.loads(match.group(0))
    return [topic] + rephrasings