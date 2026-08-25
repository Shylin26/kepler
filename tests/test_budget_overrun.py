
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.sandbox.executor import run_code_in_sandbox


result = run_code_in_sandbox("import time; time.sleep(5); print('done')", timeout=2)
print(result)