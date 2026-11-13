"""
graph/nodes/retrieve_node.py
Wraps the existing retriever (multi-query expand -> search -> rerank)
as a single LangGraph node.
"""

from models import retriever
from graph.state import ExamState


def retrieve_node(state: ExamState) -> ExamState:
    chunks = retriever.retrieve(
        state["source_name"],
        state["topic"],
        final_top_k=state.get("final_top_k", 5),
    )
    return {**state, "retrieved_chunks": chunks}