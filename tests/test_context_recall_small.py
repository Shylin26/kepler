import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama

lines = [f"Data point {i}: value={i*7}" for i in range(300)]
small_prompt = "\n".join(lines) + "\n\nWhat is the value for Data point 5? Answer with ONLY the number."

response = ollama.generate(
    model="qwen2.5-coder:7b",
    prompt=small_prompt,
    options={"num_ctx": 16384},
)
print("--- PROMPT CHARACTER COUNT ---")
print(len(small_prompt))
print("--- RAW RESPONSE (correct answer is 35) ---")
print(response["response"])
print("--- PROMPT TOKEN COUNT REPORTED ---")
print(response["prompt_eval_count"])