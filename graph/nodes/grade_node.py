"""
graph/nodes/grade_node.py
Grades a learner's submitted answers against the verified exam questions.
Pure logic, no LLM call — we already know the correct_index.
"""

from graph.state import ExamState


def grade_node(state: ExamState) -> ExamState:
    questions = state["verified_questions"]
    answers = state.get("submitted_answers") or {}

    results = []
    correct_count = 0

    for i, q in enumerate(questions):
        chosen = answers.get(str(i), answers.get(i))
        is_correct = chosen == q["correct_index"]
        if is_correct:
            correct_count += 1

        results.append({
            "question": q["question"],
            "chosen_index": chosen,
            "correct_index": q["correct_index"],
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    total = len(questions)
    percentage = round((correct_count / total) * 100, 1) if total else 0

    grading_result = {
        "score": correct_count,
        "total": total,
        "percentage": percentage,
        "results": results,
    }

    return {**state, "grading_result": grading_result}