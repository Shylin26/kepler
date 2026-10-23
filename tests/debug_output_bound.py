import statistics

from agents.coder.coder_agent import generate_code, strip_markdown_fences
from execution.sandbox.executor import run_code_in_sandbox

TASK = ("Simulate 10 steps of stochastic gradient descent (SGD) for a simple linear "
        "regression model using both a well-tuned learning rate and an extremely high "
        "learning rate. For each, use synthetic data with one feature and one target "
        "variable. Print the predicted values and loss at each step.")

RULE = ("\n\nOUTPUT RULE: keep the total printed output under 40 lines and 4000 "
        "characters. Never print lists or arrays of per-sample values; print only "
        "scalar summaries (for example the loss at each step, formatted with :.4g). "
        "If a value can grow without bound, stop the loop early once it exceeds 1e100 "
        "and print 'diverged at step N'.")

N = 8
results = {}
for label, task in (("OLD", TASK), ("NEW", TASK + RULE)):
    rows = []
    for i in range(N):
        raw, _ = generate_code(task)
        r = run_code_in_sandbox(strip_markdown_fences(raw), timeout=30)
        n = len(r["output"])
        rows.append((r["exit_code"], n))
        print(f"{label} run {i+1}: exit={r['exit_code']} output_chars={n}", flush=True)
    results[label] = rows

print("\n=== SUMMARY ===")
for label, rows in results.items():
    ok = sum(e == 0 for e, _ in rows)
    small = sum(n < 24000 for _, n in rows)
    ok_small = sum(e == 0 and n < 24000 for e, n in rows)
    print(f"{label}: exit0 {ok}/{N} | output<24000 {small}/{N} | exit0 and <24000 {ok_small}/{N} "
          f"| median chars {int(statistics.median(n for _, n in rows))}")