"""
graph/state.py
Shared state object every node in the exam-generation graph reads from
and writes to. TypedDict keeps it explicit and serializable.
"""

from typing import TypedDict, Optional


class ExamState(TypedDict, total=False):
    # inputs
    source_name: str
    topic: str
    num_questions: int
    final_top_k: int

    # working state
    expanded_queries: list[str]
    retrieved_chunks: list[dict]
    candidate_questions: list[dict]
    verified_questions: list[dict]
    rejected_log: list[dict]
    retry_count: dict  # question_index -> attempts so far

    # grading state (new — Phase 7)
    submitted_answers: Optional[dict]  # {question_index: chosen_option_index}
    grading_result: Optional[dict]
    weak_topics: list[str]