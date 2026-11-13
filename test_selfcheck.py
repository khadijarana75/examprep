from controllers import generate_controller

result = generate_controller.handle_generate(
    source_name="sample.pdf",
    topic="What method is used for denoising the beam images?",
    num_questions=3,
)

print(f"Verified questions: {len(result['questions'])}")
print(f"Rejected along the way: {result['rejected_count']}")

if result["rejected_log"]:
    print("\n--- Rejections ---")
    for r in result["rejected_log"]:
        print(f"[attempt {r['attempt']}] {r['question']}")
        print(f"  reason: {r['reason']}\n")

print("--- Final verified questions ---")
for i, q in enumerate(result["questions"], 1):
    print(f"Q{i}: {q['question']}")
    print(f"  Correct: {q['options'][q['correct_index']]}")