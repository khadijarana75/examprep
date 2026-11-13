"""
graph/nodes/self_check_node.py
Verifies each candidate question against its source. Unfaithful questions
under the retry cap get regenerated and re-queued; ones that exhaust
retries are dropped rather than served.
"""

import config
from models import self_check, question_generator
from graph.state import ExamState


def self_check_node(state: ExamState) -> ExamState:
    chunks = state["retrieved_chunks"]
    combined_source_text = "\n\n".join(c["text"] for c in chunks)

    candidates = state["candidate_questions"]
    verified = list(state.get("verified_questions", []))
    rejected_log = list(state.get("rejected_log", []))
    retry_count = dict(state.get("retry_count", {}))

    still_pending = []

    for i, q in enumerate(candidates):
        result = self_check.verify_question(q, combined_source_text)

        if result["is_faithful"]:
            verified.append(q)
            continue

        attempts = retry_count.get(i, 0)
        rejected_log.append({"question": q["question"], "reason": result["reason"], "attempt": attempts})

        if attempts < config.MAX_SELFCHECK_RETRIES:
            new_q = question_generator.regenerate_single_question(chunks, q, result["reason"])
            still_pending.append(new_q)
            retry_count[i] = attempts + 1
        # else: exhausted retries, drop silently — never served

    return {
        **state,
        "candidate_questions": still_pending,  # only unresolved ones loop back
        "verified_questions": verified,
        "rejected_log": rejected_log,
        "retry_count": retry_count,
    }


def needs_retry(state: ExamState) -> str:
    """Conditional edge: loop back to self-check if anything is still pending."""
    return "retry" if state.get("candidate_questions") else "done"