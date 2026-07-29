import ollama
import re
def generate_code(task_description: str, model: str = "qwen2.5-coder:7b") -> str:
    prompt = f"""Write a complete, runnable Python script that does the following:

{task_description}

Rules:
- Output ONLY the Python code, nothing else.
- Do NOT wrap it in markdown code fences (no ```).
- Do NOT include any explanation before or after the code.
- CRITICAL: this code will run in a bare Python 3.11 sandbox with ONLY the
  standard library available. Do NOT import numpy, pandas, matplotlib, torch,
  scipy, or any other third-party package under any circumstances, even if
  the task seems to imply them. Use only built-in modules (e.g. random, math,
  statistics, itertools). If you need "arrays," use plain Python lists. If you
  need to show a comparison, print formatted text instead of plotting.
"""

    response = ollama.generate(model=model, prompt=prompt)
    return response["response"]

import re

def strip_markdown_fences(code: str) -> str:
    
    match = re.search(r"```(?:python)?\s*\n(.*?)```", code, re.DOTALL)
    if match:
        return match.group(1).strip()
    return code.strip()

if __name__ =="__main__":
    from execution.sandbox.executor import run_code_in_sandbox
    raw=generate_code("Print the first 10 fibbonacci numbers.")
    clean=strip_markdown_fences(raw)
    print("--- CODE THE LLM WROTE ---")
    print(clean)

    result = run_code_in_sandbox(clean)

    print("--- SANDBOX EXECUTION RESULT ---")
    print(result)

