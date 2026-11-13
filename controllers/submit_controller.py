"""
submit_controller.py
Handles a learner's submitted answers: grade them, identify weak topics,
and optionally kick off a follow-up exam-generation run targeting those
topics specifically (the actual "loop" from the roadmap diagram).
"""

from graph.grading_graph import get_grading_graph
from graph.exam_graph import get_exam_graph


def handle_submit(source_name: str, verified_questions: list[dict], submitted_answers: dict) -> dict:
    grading_graph = get_grading_graph()

    result = grading_graph.invoke({
        "verified_questions": verified_questions,
        "submitted_answers": submitted_answers,
    })

    return {
        "grading_result": result["grading_result"],
        "weak_topics": result["weak_topics"],
    }


def handle_followup(source_name: str, weak_topics: list[str], num_questions: int = 3) -> dict:
    """Re-enter the exam-generation graph, topic-ing it on what was missed."""
    if not weak_topics:
        raise ValueError("No weak topics to follow up on.")

    exam_graph = get_exam_graph()
    combined_topic = "Topics the learner previously missed: " + "; ".join(weak_topics)

    result = exam_graph.invoke({
        "source_name": source_name,
        "topic": combined_topic,
        "num_questions": num_questions,
        "final_top_k": 5,
    })

    return {
        "questions": result["verified_questions"],
        "rejected_count": len(result["rejected_log"]),
    }