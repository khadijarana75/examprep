from controllers import generate_controller
from models import evaluator, retriever

source_name = "sample.pdf"
topic = "What method is used for denoising the beam images?"

gen_result = generate_controller.handle_generate(source_name, topic, num_questions=3)
questions = gen_result["questions"]

# re-run retrieval to get the chunks used (evaluator needs them for grounding)
chunks = retriever.retrieve(source_name, topic, final_top_k=gen_result["chunks_used"])

# sample.pdf is 10 pages (we've seen pages 1-10 referenced throughout testing)
report = evaluator.evaluate_exam(questions, chunks, topic, total_pages_in_doc=10)

print(f"Overall score: {report['overall']}\n")
print(f"Faithfulness avg: {report['faithfulness']['average']}")
for s in report['faithfulness']['per_question']:
    print(f"  {s['score']}  — {s['reason']}")

print(f"\nDistractor plausibility avg: {report['distractor_plausibility']['average']}")
for s in report['distractor_plausibility']['per_question']:
    print(f"  {s['score']}  — {s['reason']}")

print(f"\nContext precision: {report['context_precision']['score']}")
print(f"Context coverage: {report['context_coverage']['score']} ({report['context_coverage']['distinct_pages']}/{report['context_coverage']['total_pages']} pages)")
