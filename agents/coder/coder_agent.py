import ollama
import re
def generate_code(task_description:str,model:str="qwen2.5-coder:7b")->str:
    prompt = f"""Write a complete, runnable Python script that does the following:

{task_description}

Rules:
- Output ONLY the Python code, nothing else.
- Do NOT wrap it in markdown code fences (no ```).
- Do NOT include any explanation before or after the code.
- The script must run standalone with only Python's standard library, unless the task explicitly requires a specific package.
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

