"""
generate_controller.py
Thin wrapper around the compiled LangGraph exam-generation graph.
"""

from graph.exam_graph import get_exam_graph


def handle_generate(source_name: str, topic: str, num_questions: int = 3, final_top_k: int = 5) -> dict:
    graph = get_exam_graph()

    result = graph.invoke({
        "source_name": source_name,
        "topic": topic,
        "num_questions": num_questions,
        "final_top_k": final_top_k,
    })

    if not result.get("retrieved_chunks"):
        raise ValueError(
            f"No relevant content found for topic '{topic}' in '{source_name}'. "
            f"Has this document been uploaded and indexed?"
        )

    return {
        "source": source_name,
        "topic": topic,
        "chunks_used": len(result["retrieved_chunks"]),
        "questions": result["verified_questions"],
        "rejected_count": len(result["rejected_log"]),
        "rejected_log": result["rejected_log"],
    }