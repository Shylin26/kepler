import json
import sys

for q in json.load(open(sys.argv[1])):
    print("=====", q["id"], "| attempts:", q["attempts"])
    for c in q["critic_history"]:
        r = c["reason"]
        if r.startswith("Non-zero exit code"):
            kind = "CRASH"
        elif r.startswith("Code was killed"):
            kind = "RUNAWAY-KILL"
        elif r.startswith(("Script ran successfully", "Output contains")):
            kind = "NO-OUTPUT/TRACEBACK"
        else:
            kind = "CRITIC-LLM-REJECTION"
        print(f"  attempt {c['attempt']} [{kind}]: {r[-260:]!r}")