"""
question_generator.py
Turns retrieved+reranked chunks into structured MCQ questions with
distractors, using Groq. First real "generation" step in the pipeline.
"""

import json
import re
import time
import requests
import config

OPTIONS_PER_QUESTION = 4


class LLMError(Exception):
    pass


def _call_groq(system_prompt: str, user_prompt: str, temperature: float = 0.4, max_retries: int = 3) -> str:
    if not config.GROQ_API_KEY:
        raise LLMError(
            "GROQ_API_KEY is not set. Add it to your .env file before generating quizzes."
        )

    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.GROQ_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    for attempt in range(max_retries + 1):
        resp = requests.post(config.GROQ_API_URL, headers=headers, json=payload, timeout=60)

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]

        if resp.status_code == 429 and attempt < max_retries:
            wait_match = re.search(r"try again in ([\d.]+)s", resp.text)
            wait_seconds = float(wait_match.group(1)) if wait_match else (2 ** attempt)
            time.sleep(wait_seconds + 0.5)
            continue

        raise LLMError(f"Groq API error {resp.status_code}: {resp.text[:300]}")

    raise LLMError("Groq rate limit persisted after all retries.")


def _extract_json(raw: str):
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"(\[.*\]|\{.*\})", cleaned, flags=re.DOTALL)
    if not match:
        raise LLMError(f"Could not find JSON in LLM response: {raw[:300]}")
    return json.loads(match.group(1))


QUESTION_SYSTEM_PROMPT = f"""You are an exam-writing assistant. Generate multiple-choice \
questions strictly from the SOURCE CHUNKS provided, which come from a real document. Rules:
- Every question must be answerable using only the source chunks given.
- Each question has exactly {OPTIONS_PER_QUESTION} options, only ONE correct.
- Distractors must be plausible — drawn from related concepts actually present in the \
source chunks, not silly or obviously wrong.
- Include the source page number (given with each chunk) in your answer.
- Respond with ONLY a raw JSON array, no markdown fences, no preamble, no reasoning text. Format:
[
  {{
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "correct_index": 0,
    "explanation": "short explanation citing the source",
    "source_page": 5
  }}
]
"""


def generate_questions(chunks: list[dict], num_questions: int = 3) -> list[dict]:
    if not chunks:
        raise ValueError("No chunks provided to generate questions from.")

    context_blocks = []
    for c in chunks:
        page = c["metadata"].get("page", "unknown")
        context_blocks.append(f"[Page {page}]\n{c['text']}")

    user_prompt = (
        f"Number of questions to generate: {num_questions}\n\n"
        f"SOURCE CHUNKS:\n\n" + "\n\n---\n\n".join(context_blocks)
    )

    raw = _call_groq(QUESTION_SYSTEM_PROMPT, user_prompt)
    questions = _extract_json(raw)

    if not isinstance(questions, list) or not questions:
        raise LLMError("LLM did not return a valid question list.")

    return questions


def regenerate_single_question(chunks: list[dict], failed_question: dict, reason: str) -> dict:
    context_blocks = []
    for c in chunks:
        page = c["metadata"].get("page", "unknown")
        context_blocks.append(f"[Page {page}]\n{c['text']}")

    user_prompt = (
        f"Your previous question was rejected as not grounded in the source. "
        f"Rejection reason: {reason}\n\n"
        f"Previous (rejected) question: {failed_question['question']}\n\n"
        f"Generate ONE new, corrected question on a similar topic, strictly grounded "
        f"in the source chunks below. Same JSON format as before, but return a JSON "
        f"ARRAY containing exactly one question object.\n\n"
        f"SOURCE CHUNKS:\n\n" + "\n\n---\n\n".join(context_blocks)
    )

    raw = _call_groq(QUESTION_SYSTEM_PROMPT, user_prompt)
    questions = _extract_json(raw)

    if not isinstance(questions, list) or not questions:
        raise LLMError("Regeneration did not return a valid question.")

    return questions[0]