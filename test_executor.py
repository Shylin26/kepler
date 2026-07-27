from execution.sandbox.executor import run_code_in_sandbox

result = run_code_in_sandbox("print('hello from inside the sandbox')")
print(result)

result = run_code_in_sandbox("import time; time.sleep(60)", timeout=5)
print(result)