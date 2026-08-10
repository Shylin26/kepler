import sys
import os
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.analyst.analyst_agent import check_grounding

real_output = "LR=0.01 Accuracy: 1.00\nLR=0.1 Accuracy: 1.00\nAdversarial Accuracy: 0.57"

cases = [
    ("exact match (control)",          "Adversarial Accuracy: 0.57"),
    ("trailing period added",          "Adversarial Accuracy: 0.57."),
    ("line-break normalized to space", "LR=0.1 Accuracy: 1.00 Adversarial Accuracy: 0.57"),
    ("number reformatted (0.570)",     "Adversarial Accuracy: 0.570"),
    ("trailing % added",               "Adversarial Accuracy: 0.57%"),
    ("extra whitespace collapsed",     "Adversarial  Accuracy: 0.57"),
]

for label, quote in cases:
    result = check_grounding(quote, real_output)
    print(f"{label:35s} -> grounded={result['grounded']}")

    