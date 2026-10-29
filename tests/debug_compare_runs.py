import json
import sys

files = sys.argv[1:]
runs = [json.load(open(f)) for f in files]
print("files:", [f.split("results_")[1][:16] for f in files])
for qid in [q["id"] for q in runs[0]]:
    cells = []
    for r in runs:
        q = next(x for x in r if x["id"] == qid)
        if q["coder_sandbox_valid"]:
            cells.append(f"{q['analyst_verdict']}({'match' if q['verdict_match'] else 'miss'}, attempts={q['attempts']})")
        else:
            cells.append(f"no-verdict(attempts={q['attempts']})")
    print(f"{qid}: " + " | ".join(cells))
for i, r in enumerate(runs):
    reached = sum(bool(q["coder_sandbox_valid"]) for q in r)
    matched = sum(bool(q["verdict_match"]) for q in r)
    print(f"run {i+1}: reached a verdict {reached}/5 | matches {matched}/5 | "
          f"has final_sandbox_output: {'final_sandbox_output' in r[0]}")