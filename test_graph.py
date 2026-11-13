from graph.exam_graph import get_exam_graph

graph = get_exam_graph()

result = graph.invoke({
    "source_name": "sample.pdf",
    "topic": "What method is used for denoising the beam images?",
    "num_questions": 3,
    "final_top_k": 5,
})

print(f"Verified questions: {len(result['verified_questions'])}")
print(f"Rejected along the way: {len(result['rejected_log'])}")

for i, q in enumerate(result["verified_questions"], 1):
    print(f"\nQ{i}: {q['question']}")
    print(f"  Correct: {q['options'][q['correct_index']]}")