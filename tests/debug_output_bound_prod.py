import statistics

from agents.coder.coder_agent import generate_code, strip_markdown_fences
from execution.sandbox.executor import run_code_in_sandbox

TASK = ("Simulate 10 steps of stochastic gradient descent (SGD) for a simple linear "
        "regression model using both a well-tuned learning rate and an extremely high "
        "learning rate. For each, use synthetic data with one feature and one target "
        "variable. Print the predicted values and loss at each step.")

N = 8
rows = []
for i in range(N):
    raw, _ = generate_code(TASK)
    r = run_code_in_sandbox(strip_markdown_fences(raw), timeout=30)
    rows.append((r["exit_code"], len(r["output"]), r["output"]))
    print(f"run {i+1}: exit={r['exit_code']} output_chars={len(r['output'])}", flush=True)

ok_small = sum(e == 0 and n < 24000 for e, n, _ in rows)
print(f"\n=== exit0 and <24000: {ok_small}/{N} | median chars {int(statistics.median(n for _, n, _ in rows))} ===")
for k, (e, n, o) in enumerate(rows[:3], 1):
    print(f"\n#### output of run {k} (exit {e}, {n} chars)\n{o[:1200]}")