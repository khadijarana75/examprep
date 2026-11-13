"""
graph/nodes/weak_topics_node.py
Pulls the actual missed questions out of the grading result so the
generation side of the graph can be re-invoked targeting just those topics.
"""

from graph.state import ExamState


def identify_weak_topics_node(state: ExamState) -> ExamState:
    grading = state.get("grading_result") or {}
    results = grading.get("results", [])

    weak = [r["question"] for r in results if not r["is_correct"]]

    return {**state, "weak_topics": weak}


def has_weak_topics(state: ExamState) -> str:
    """Conditional edge: only loop back into generation if something was missed."""
    return "weak" if state.get("weak_topics") else "none"