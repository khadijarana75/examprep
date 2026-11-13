"""
graph/exam_graph.py
The exam-generation graph: retrieve -> generate -> self-check, with a
conditional loop back into self-check for regenerated questions.
"""

from langgraph.graph import StateGraph, END
from graph.state import ExamState
from graph.nodes.retrieve_node import retrieve_node
from graph.nodes.generate_node import generate_node
from graph.nodes.self_check_node import self_check_node, needs_retry


def build_exam_graph():
    graph = StateGraph(ExamState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("self_check", self_check_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "self_check")

    graph.add_conditional_edges(
        "self_check",
        needs_retry,
        {"retry": "self_check", "done": END},
    )

    return graph.compile()


_compiled_graph = None


def get_exam_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_exam_graph()
    return _compiled_graph
