import ast
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "benchmark/run_log_q1q5_20261017T122022.txt"
n = 0
for line in open(path):
    if line.startswith("{'exit_code'"):
        d = ast.literal_eval(line.strip())
        n += 1
        o = d["output"]
        print("#### sandbox result", n, "exit", d["exit_code"], "len", len(o))
        print(o[:400].replace("\n", " | "))
        print("   ...")
        print(o[-400:].replace("\n", " | "))