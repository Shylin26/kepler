import sys

path = sys.argv[1]
wanted = [int(a) for a in sys.argv[2:]]
blocks = open(path).read().split("--- CODE ---")[1:]
for i, b in enumerate(blocks, 1):
    if wanted and i not in wanted:
        continue
    print(f"######## code block {i}")
    print(b.split("--- SANDBOX RESULT ---")[0].strip()[:1800])