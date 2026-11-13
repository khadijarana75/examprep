from models import retriever

source_name = "sample.pdf"
topic = "What method is used for denoising the beam images?"

results = retriever.retrieve(source_name, topic)

print(f"Final results: {len(results)}")
for r in results:
    print(f"\nrerank_score={r['rerank_score']:.4f} page={r['metadata']['page']}")
    print(r["text"][:200])