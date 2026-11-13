"""
evaluator.py
Unit 14 — RAGAS-style evaluation, implemented as Groq LLM-as-judge calls
rather than the ragas package (which assumes an OpenAI-shaped stack).
Four metrics, each scored 0.0-1.0:
  - faithfulness: does the marked-correct answer actually follow from its cited chunk
  - context_precision: how much of the retrieved context was actually relevant
  - context_coverage: how much of the document's page/section range the exam spans
    (our proxy for "context recall" — there's no single ground-truth answer set
    to recall against here, so we measure topic breadth instead)
  - distractor_plausibility: are wrong options drawn from related concepts, not noise
"""

import json
import re
import time
import requests
import config


class LLMError(Exception):
    pass


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
            wait_match = re.search(r"try again in ([\d.]+)s", resp.text)
            wait_seconds = float(wait_match.group(1)) if wait_match else (2 ** attempt)
            time.sleep(wait_seconds + 0.5)
            continue
        raise LLMError(f"Groq API error {resp.status_code}: {resp.text[:300]}")

    raise LLMError("Groq rate limit persisted after all retries.")


def _extract_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise LLMError(f"Could not find JSON object in response: {raw[:300]}")
    return json.loads(match.group(0))


# --- Faithfulness -----------------------------------------------------------

FAITHFULNESS_PROMPT = """Rate how well the marked-correct ANSWER is supported by the \
SOURCE TEXT, on a scale of 0.0 to 1.0:
- 1.0 = directly and clearly stated in the source
- 0.5 = plausible but requires inference beyond what's stated
- 0.0 = not supported, or contradicted by the source

Respond with ONLY raw JSON: {"score": 0.0, "reason": "short reason"}
"""


def score_faithfulness(question: dict, source_text: str) -> dict:
    correct_answer = question["options"][question["correct_index"]]
    user_prompt = f"SOURCE TEXT:\n{source_text}\n\nQUESTION: {question['question']}\nANSWER: {correct_answer}"
    result = _extract_json(_call_groq(FAITHFULNESS_PROMPT, user_prompt))
    return {"score": float(result["score"]), "reason": result.get("reason", "")}


# --- Context precision --------------------------------------------------------

PRECISION_PROMPT = """Given a TOPIC and a RETRIEVED CHUNK, rate how relevant the chunk \
is to generating exam questions about that topic, 0.0 to 1.0:
- 1.0 = directly on-topic, clearly usable
- 0.5 = tangentially related
- 0.0 = irrelevant noise (references, page headers, unrelated section)

Respond with ONLY raw JSON: {"score": 0.0}
"""


def score_context_precision(topic: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {"score": 0.0, "per_chunk": []}

    per_chunk = []
    for c in chunks:
        user_prompt = f"TOPIC: {topic}\n\nCHUNK:\n{c['text'][:500]}"
        result = _extract_json(_call_groq(PRECISION_PROMPT, user_prompt))
        per_chunk.append({"page": c["metadata"].get("page"), "score": float(result["score"])})

    avg = sum(p["score"] for p in per_chunk) / len(per_chunk)
    return {"score": round(avg, 3), "per_chunk": per_chunk}


# --- Context coverage (our "recall" proxy) -------------------------------------

def score_context_coverage(chunks: list[dict], total_pages_in_doc: int) -> dict:
    """
    No single ground-truth answer set exists to recall against here, so we
    proxy recall with topic breadth: how much of the document's page range
    a generated exam actually drew from, vs. clustering on one page.
    """
    if not chunks or not total_pages_in_doc:
        return {"score": 0.0, "distinct_pages": 0, "total_pages": total_pages_in_doc}

    distinct_pages = len({c["metadata"].get("page") for c in chunks if c["metadata"].get("page")})
    score = min(1.0, distinct_pages / min(total_pages_in_doc, len(chunks)))
    return {"score": round(score, 3), "distinct_pages": distinct_pages, "total_pages": total_pages_in_doc}


# --- Distractor plausibility ---------------------------------------------------

DISTRACTOR_PROMPT = """Rate the quality of this multiple-choice question's WRONG options \
(distractors), 0.0 to 1.0:
- 1.0 = distractors are plausible, drawn from related real concepts, could fool someone \
who half-knows the material
- 0.5 = mixed — some plausible, some obviously wrong
- 0.0 = distractors are nonsense, unrelated, or so implausible no one would pick them

Respond with ONLY raw JSON: {"score": 0.0, "reason": "short reason"}
"""


def score_distractor_plausibility(question: dict) -> dict:
    distractors = [opt for i, opt in enumerate(question["options"]) if i != question["correct_index"]]
    user_prompt = (
        f"QUESTION: {question['question']}\n"
        f"CORRECT ANSWER: {question['options'][question['correct_index']]}\n"
        f"DISTRACTORS: {', '.join(distractors)}"
    )
    result = _extract_json(_call_groq(DISTRACTOR_PROMPT, user_prompt))
    return {"score": float(result["score"]), "reason": result.get("reason", "")}


# --- Full exam evaluation --------------------------------------------------------

def evaluate_exam(questions: list[dict], chunks: list[dict], topic: str, total_pages_in_doc: int) -> dict:
    """Runs all four metrics across a generated exam and returns an aggregate report."""
    combined_source_text = "\n\n".join(c["text"] for c in chunks)

    faithfulness_scores = [score_faithfulness(q, combined_source_text) for q in questions]
    distractor_scores = [score_distractor_plausibility(q) for q in questions]
    precision = score_context_precision(topic, chunks)
    coverage = score_context_coverage(chunks, total_pages_in_doc)

    avg_faithfulness = sum(s["score"] for s in faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0
    avg_distractor = sum(s["score"] for s in distractor_scores) / len(distractor_scores) if distractor_scores else 0

    return {
        "faithfulness": {"average": round(avg_faithfulness, 3), "per_question": faithfulness_scores},
        "distractor_plausibility": {"average": round(avg_distractor, 3), "per_question": distractor_scores},
        "context_precision": precision,
        "context_coverage": coverage,
        "overall": round((avg_faithfulness + avg_distractor + precision["score"] + coverage["score"]) / 4, 3),
    }