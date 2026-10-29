import json
import sys

qid = sys.argv[1]
for path in sys.argv[2:]:
    q = next(x for x in json.load(open(path)) if x["id"] == qid)
    print("#####", path.split("results_")[1][:16], "| verdict:", q["analyst_verdict"], "| attempts:", q["attempts"])
    print("TASK:", q["planner_task_description"][:300].replace("\n", " "))
    print("OUTPUT:", q.get("final_sandbox_output", "")[:500].replace("\n", " | "))
    print("REASONING:", (q["analyst_reasoning"] or "")[:400].replace("\n", " "))