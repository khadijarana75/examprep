from models import retriever, question_generator

source_name = "sample.pdf"
topic = "What method is used for denoising the beam images?"

chunks = retriever.retrieve(source_name, topic, final_top_k=4)
print(f"Retrieved {len(chunks)} chunks for generation")

questions = question_generator.generate_questions(chunks, num_questions=3)

print(f"\nGenerated {len(questions)} questions\n")
for i, q in enumerate(questions, 1):
    print(f"Q{i}: {q['question']}")
    for j, opt in enumerate(q['options']):
        marker = "✓" if j == q['correct_index'] else " "
        print(f"  [{marker}] {opt}")
    print(f"  Explanation: {q['explanation']}")
    print(f"  Source page: {q['source_page']}\n")