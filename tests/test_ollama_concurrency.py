import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import ollama
from concurrent.futures import ThreadPoolExecutor

PROMPT = "Write a one-sentence description of gradient descent."
MODEL = "qwen2.5-coder:7b"

def single_call(i):
    start = time.monotonic()
    response = ollama.generate(model=MODEL, prompt=PROMPT)
    duration = time.monotonic() - start
    return {"call": i, "wall_clock_seconds": round(duration, 2), "reported_total_duration_seconds": round((response["total_duration"] or 0) / 1e9, 2)}

# Warm the model first so load_duration doesn't skew the first call
ollama.generate(model=MODEL, prompt="warm up")

print("=== SEQUENTIAL (3 calls, one after another) ===")
seq_start = time.monotonic()
for i in range(3):
    print(single_call(i))
seq_total = time.monotonic() - seq_start
print(f"Sequential total wall-clock: {seq_total:.2f}s\n")

print("=== CONCURRENT (3 calls fired at once via threads) ===")
conc_start = time.monotonic()
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(single_call, range(3)))
for r in results:
    print(r)
conc_total = time.monotonic() - conc_start
print(f"Concurrent total wall-clock: {conc_total:.2f}s")