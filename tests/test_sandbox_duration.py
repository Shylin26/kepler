import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.sandbox.executor import run_code_in_sandbox


result = run_code_in_sandbox("import time; time.sleep(2); print('done')", timeout=30)
print(result)