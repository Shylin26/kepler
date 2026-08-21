import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst.analyst_agent import check_grounding


real_output_line = "Step 2 (Momentum): theta_0 = 0.9278508718468521, theta_1 = 3.093919453858705, error = 46.2599"
fabricated_quote = "Step 2 (Momentum): theta_0 = 1.9278508718468521, theta_1 = 3.093919453858705, error = 46.2599"

result = check_grounding(fabricated_quote, real_output_line)
print(result)
assert result["grounded"] is False, "Expected the digit-transcription-error quote to be rejected as ungrounded"
print("PASS: real-world digit transcription error correctly caught")