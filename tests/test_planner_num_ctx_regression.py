"""
Regression test for Planner's plan_experiment(): confirms num_ctx=32768 was
added without breaking normal operation. Unlike Critic/Coder/Director/Analyst,
this prompt has no unbounded growth mechanism (no retry history, no
accumulating list, no unbounded output field) -- research_question and the
static example JSON keep this prompt naturally short. Padding it artificially
to simulate truncation risk would test a scenario that can't realistically
occur here, so this test instead confirms the fix is inert: a normal call
still produces a valid, correctly-typed ExperimentSpec.
"""

from agents.planner.planner_agent import plan_experiment
from schemas.experiment_spec import ExperimentSpec

def test_plan_experiment_still_works_with_num_ctx_set():
    spec = plan_experiment(
        "Does using a smaller batch size lead to noisier but faster-converging training loss?"
    )

    print("--- SPEC ---")
    print(spec.model_dump_json(indent=2))

    assert isinstance(spec, ExperimentSpec), "plan_experiment() did not return an ExperimentSpec"
    assert spec.task_description.strip(), "task_description is empty"
    assert spec.hypothesis.strip(), "hypothesis is empty"
    assert isinstance(spec.compute_budget_seconds, int) and spec.compute_budget_seconds > 0, (
        "compute_budget_seconds is missing or not a positive int"
    )

    print("PASS: plan_experiment() still returns a valid ExperimentSpec with num_ctx=32768 set. "
          "Note: this prompt has no realistic truncation-risk scenario (unlike the other five "
          "call sites), so this test confirms the fix is inert rather than stress-testing "
          "truncation specifically.")

if __name__ == "__main__":
    test_plan_experiment_still_works_with_num_ctx_set()