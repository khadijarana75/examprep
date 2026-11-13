from controllers import generate_controller, submit_controller

# generate a real exam first
gen_result = generate_controller.handle_generate(
    source_name="sample.pdf",
    topic="What method is used for denoising the beam images?",
    num_questions=3,
)
questions = gen_result["questions"]

print(f"Generated {len(questions)} questions\n")
for i, q in enumerate(questions):
    print(f"Q{i}: {q['question']}")
    print(f"   Correct index: {q['correct_index']}\n")

# simulate a learner deliberately getting question 0 WRONG, rest right
fake_answers = {}
for i, q in enumerate(questions):
    fake_answers[str(i)] = q["correct_index"] if i != 0 else (q["correct_index"] + 1) % len(q["options"])

submit_result = submit_controller.handle_submit("sample.pdf", questions, fake_answers)
print("--- Grading result ---")
print(f"Score: {submit_result['grading_result']['score']}/{submit_result['grading_result']['total']}")
print(f"Weak topics: {submit_result['weak_topics']}")

if submit_result["weak_topics"]:
    followup = submit_controller.handle_followup("sample.pdf", submit_result["weak_topics"])
    print(f"\n--- Follow-up questions ({len(followup['questions'])}) ---")
    for q in followup["questions"]:
        print(f"- {q['question']}")