"""
graph/grading_graph.py
A second small graph: grade -> identify weak topics. Kept separate from
the exam-generation graph since it runs at a different time (after the
learner submits answers, not during initial generation) and the
roadmap's own diagram shows it entering the SAME ExpandQuery node the
generation graph starts from — that re-entry happens at the controller
level (Phase 7's real "loop"), not by merging the graphs into one.
"""

from langgraph.graph import StateGraph, END
from graph.state import ExamState
from graph.nodes.grade_node import grade_node
from graph.nodes.weak_topics_node import identify_weak_topics_node


def build_grading_graph():
    graph = StateGraph(ExamState)

    graph.add_node("grade", grade_node)
    graph.add_node("identify_weak_topics", identify_weak_topics_node)

    graph.set_entry_point("grade")
    graph.add_edge("grade", "identify_weak_topics")
    graph.add_edge("identify_weak_topics", END)

    return graph.compile()


_compiled_grading_graph = None


def get_grading_graph():
    global _compiled_grading_graph
    if _compiled_grading_graph is None:
        _compiled_grading_graph = build_grading_graph()
    return _compiled_grading_graph