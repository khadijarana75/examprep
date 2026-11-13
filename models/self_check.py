"""
self_check.py
Unit 10 — Self-Improving Pipelines: reflection/self-critique.
Verifies each generated question is actually supported by its cited
source chunk before it reaches the learner. This is the guard against
the LLM inventing a plausible-sounding but ungrounded "correct" answer.
"""

import json
import re
import time
import requests
import config


class LLMError(Exception):
    pass


import time
import re


def _call_groq(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.GROQ_MODEL,
        "temperature": 0.0,
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
            # Groq's error body names the exact wait time, e.g. "try again in 3.915s"
            wait_match = re.search(r"try again in ([\d.]+)s", resp.text)
            wait_seconds = float(wait_match.group(1)) if wait_match else (2 ** attempt)
            time.sleep(wait_seconds + 0.5)  # small buffer past what Groq asked for
            continue

        raise LLMError(f"Groq API error {resp.status_code}: {resp.text[:300]}")

    raise LLMError("Groq rate limit persisted after all retries.")


def _extract_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise LLMError(f"Could not find JSON object in response: {raw[:300]}")
    return json.loads(match.group(0))


SELFCHECK_SYSTEM_PROMPT = """You are a strict fact-checker for exam questions. Given a \
SOURCE TEXT and a QUESTION with its marked-correct ANSWER, determine whether the source \
text actually supports that answer as correct.

Be strict: if the source text doesn't clearly state or imply the answer, mark it unfaithful.
If the source text contradicts the marked answer, mark it unfaithful.

Respond with ONLY a raw JSON object, no markdown fences, no preamble:
{"is_faithful": true, "reason": "short reason"}
or
{"is_faithful": false, "reason": "short reason explaining what's wrong"}
"""


def verify_question(question: dict, source_text: str) -> dict:
    """
    question: {"question", "options", "correct_index", "explanation", "source_page"}
    source_text: the raw text of the chunk(s) this question was generated from
    Returns {"is_faithful": bool, "reason": str}
    """
    correct_answer = question["options"][question["correct_index"]]

    user_prompt = (
        f"SOURCE TEXT:\n{source_text}\n\n"
        f"QUESTION: {question['question']}\n"
        f"MARKED-CORRECT ANSWER: {correct_answer}\n"
    )

    raw = _call_groq(SELFCHECK_SYSTEM_PROMPT, user_prompt)
    result = _extract_json(raw)

    if "is_faithful" not in result:
        raise LLMError(f"Self-check response missing 'is_faithful': {result}")

    return result