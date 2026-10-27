import json
import re
from unittest.mock import patch

import ollama
import agents.coder.coder_agent as cg
from agents.coder.coder_agent import generate_code, strip_markdown_fences, check_syntax
from execution.sandbox.executor import run_code_in_sandbox

RESULTS = "benchmark/results_20261025T121757Z.json"
N = 3
tasks = [(q["id"], q["planner_task_description"]) for q in json.load(open(RESULTS))]
RULE_RE = re.compile(r"- OUTPUT SIZE:.*?'diverged at step N'\.\n", re.S)
real = ollama.generate


def make_gen(strip):
    def gen(**kw):
        if strip:
            kw["prompt"] = RULE_RE.sub("", kw["prompt"])
        assert ("OUTPUT SIZE" in kw["prompt"]) != strip, "rule state does not match the arm"
        return real(**kw)
    return gen


def one(task, strip):
    with patch.object(cg.ollama, "generate", make_gen(strip)):
        raw, _ = generate_code(task)
    code = strip_markdown_fences(raw)
    if not check_syntax(code)["valid"]:
        return "syntax_error", 0
    r = run_code_in_sandbox(code, timeout=30)
    err = ""
    if r["exit_code"] != 0:
        m = re.findall(r"^(\w*(?:Error|Exception))", r["output"], re.M)
        err = m[-1] if m else "crash"
    return (err or "ok"), len(r["output"])


tally = {"WITH_RULE": {}, "NO_RULE": {}}
for name, task in tasks:
    for i in range(N):
        for label, strip in (("WITH_RULE", False), ("NO_RULE", True)):
            res, n = one(task, strip)
            tally[label].setdefault(name, []).append(res)
            print(f"{name} run {i+1} {label}: {res} ({n} chars)", flush=True)

print("\n=== EXIT-0 COUNTS (single attempt, no retries) ===")
for label, d in tally.items():
    per = {k: sum(v == "ok" for v in vs) for k, vs in d.items()}
    print(f"{label}: {sum(per.values())}/{N * len(tasks)} | per task {per}")