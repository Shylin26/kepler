import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
import run_loop
from schemas.experiment_spec import ExperimentSpec

# Real ExperimentSpec (not a stub) so spec.model_dump() works if we later
# want to feed this into log_trajectory too. Budget is deliberately tiny
# (0.1s) -- real sandbox calls have ~0.3-0.5s of container overhead each
# (confirmed earlier via test_sandbox_duration.py), so 3 real attempts
# should comfortably exceed it.
spec = ExperimentSpec(
    hypothesis="Test hypothesis for budget flag verification.",
    task_description="Print the string 'hi'.",
    expected_outcome="Output contains 'hi'.",
    success_criteria="Output is exactly 'hi'.",
    compute_budget_seconds=1,
    notes="Synthetic test spec, not a real experiment.",
)

with patch("run_loop.generate_code", return_value="import time; time.sleep(0.5); print('hi')"), \
     patch("run_loop.basic_sanity_check", return_value={"passed": False, "reason": "forced failure to exhaust all attempts"}):
    result = run_loop.run_with_self_correction(spec, max_attempts=3)