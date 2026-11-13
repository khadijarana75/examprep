from models.regression import run_regression_suite

report = run_regression_suite()

print(f"Regression suite: {report['passed']}/{report['total']} passed\n")

for r in report["results"]:
    status = "PASS" if r["passed"] else "FAIL"
    print(f"[{status}] {r['topic']}")
    if "all_questions" in r:
        for q_text in r["all_questions"]:
            print(f"   - {q_text}")
        hit_note = r["direct_hit"] if r["direct_hit"] else "(none — retrieval found it, LLM asked about something else instead)"
        print(f"   Direct hit on golden fact: {hit_note}")
        print(f"   Faithfulness avg: {r['faithfulness_avg']}  Distractor avg: {r['distractor_avg']}")
        print(f"   Checks: {r['checks']}")
    else:
        print(f"   {r['reason']}")
    print()