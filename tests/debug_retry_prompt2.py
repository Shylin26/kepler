from agents.coder.coder_agent import generate_code, strip_markdown_fences
from execution.sandbox.executor import run_code_in_sandbox
from run_loop import build_retry_prompt
from tests.debug_retry_prompt import TASK, BAD

REASON = ('Non-zero exit code: 1. Output: Traceback (most recent call last): | '
          '  File "<string>", line 31, in <module> |   File "<string>", line 31, in <listcomp> | '
          "  File \"<string>\", line 6, in sigmoid | NameError: name 'math' is not defined")

OLD = f"""{TASK}
Your previous attempt failed. Here is the code you wrote:
{BAD}

Here is why it failed:
{REASON}

Please fix the code and provide a corrected, complete script."""
NEW = build_retry_prompt(TASK, BAD, REASON)

for label, prompt in (("OLD", OLD), ("NEW", NEW)):
    ok = 0
    for i in range(5):
        raw, _ = generate_code(prompt)
        r = run_code_in_sandbox(strip_markdown_fences(raw), timeout=30)
        good = r["exit_code"] == 0
        ok += good
        print(f"{label} run {i+1}: exit={r['exit_code']}")
    print(f"=== {label}: {ok}/5 ran successfully ===")