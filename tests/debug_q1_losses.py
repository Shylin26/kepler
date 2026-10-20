import ast
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "benchmark/run_log_q1q5_20261017T122022.txt"
n = 0
for line in open(path):
    if line.startswith("{'exit_code'"):
        d = ast.literal_eval(line.strip())
        if d["exit_code"] != 0:
            continue
        n += 1
        print(f"#### Q1 attempt {n}")
        section = None
        losses = []
        for out_line in d["output"].split("\n"):
            m = re.match(r"Step (\d+): Loss = ([-\d.e+]+)", out_line)
            if m:
                losses.append(m.group(2))
            elif out_line.strip():
                if section is not None:
                    print(f"  [{section}] losses:", ", ".join(losses))
                section, losses = out_line.strip()[:40], []
        print(f"  [{section}] losses:", ", ".join(losses))
    elif line.startswith("{'passed'"):
        v = ast.literal_eval(line.strip())
        cost = v.get("llm_cost")
        if cost:
            print("   Critic prompt_tokens:", cost["prompt_tokens"], "| passed:", v["passed"])