import re
from unittest.mock import patch

import ollama
import agents.planner.planner_agent as pa
from benchmark.planted_questions import PLANTED_QUESTIONS

Q1 = next(q.research_question for q in PLANTED_QUESTIONS if q.id == "lr_divergence_01")
QUESTIONS = [
    ("q1", Q1),
    ("heldout_small_lr", "Does a very small learning rate make gradient descent on a simple "
                         "quadratic loss converge more slowly than a moderate learning rate?"),
    ("heldout_10x", "Does increasing the learning rate by 10x speed up convergence of gradient "
                    "descent on simple linear regression, as long as training stays stable?"),
]

RULE = ("LEARNING-RATE RULE: if the experiment compares learning rates, write each learning "
        "rate as an explicit number in the task_description (for example 0.01 and 1.0). Never "
        "describe a learning rate only in words such as 'well-tuned' or 'extremely high'. If "
        "the question specifies a multiple (for example 100x), use that exact multiple.")

KEY = re.compile(r"learning[- ]rates?|\blr\b|alpha", re.I)
NUM = re.compile(r"(?<![\w.])\d*\.?\d+(?:[eE]-?\d+)?")
N = 5


def lr_values(text):
    vals = set()
    for m in KEY.finditer(text):
        for n in NUM.findall(text[m.end(): m.end() + 80]):
            vals.add(float(n))
    return sorted(vals)


def run_arm(label, rule):
    real = ollama.generate

    def gen(**kw):
        if rule:
            kw["prompt"] = kw["prompt"].replace(
                "Research question:", rule + "\n\nResearch question:", 1)
        return real(**kw)

    concrete = fails = 0
    with patch.object(pa.ollama, "generate", gen):
        for name, q in QUESTIONS:
            for i in range(N):
                try:
                    spec, _ = pa.plan_experiment(q)
                except Exception as e:
                    fails += 1
                    print(f"{label} {name} run {i+1}: PARSE FAIL ({type(e).__name__})", flush=True)
                    continue
                vals = lr_values(spec.task_description)
                ok = len(vals) >= 2
                concrete += ok
                print(f"{label} {name} run {i+1}: values={vals} concrete={ok}", flush=True)
                if i == 0:
                    print("    TASK:", spec.task_description[:300].replace("\n", " "), flush=True)
    total = N * len(QUESTIONS)
    print(f"=== {label}: concrete {concrete}/{total} | parse failures {fails} ===\n", flush=True)
    return concrete, fails


old = run_arm("OLD", "")
new = run_arm("NEW", RULE)
print("DECISION: adopt only if NEW concrete >= OLD concrete + 4 AND NEW parse failures <= OLD + 1")
print("OLD", old, "NEW", new)