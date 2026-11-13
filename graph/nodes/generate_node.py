"""
graph/nodes/generate_node.py
Generates the initial candidate questions from retrieved chunks.
"""

from models import question_generator
from graph.state import ExamState


def generate_node(state: ExamState) -> ExamState:
    questions = question_generator.generate_questions(
        state["retrieved_chunks"],
        num_questions=state.get("num_questions", 3),
    )
    return {
        **state,
        "candidate_questions": questions,
        "verified_questions": [],
        "rejected_log": [],
        "retry_count": {i: 0 for i in range(len(questions))},
    }