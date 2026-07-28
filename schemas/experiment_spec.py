from pydantic import BaseModel, Field
from typing import Optional

class ExperimentSpec(BaseModel):
    hypothesis: str=Field(
        description="The specific, falsifiable claim this experiment tests."
    )
    task_description:str=Field(
        description="A precise,self-contained instruction for what code to write."
                    "Must be precise enough that no further clarification is required."
    )
    expected_outcome:str=Field(
        description="What result would support the hypothesis,states concretly"
                    "(e.g. 'training loss should be lower than the baseline by epoch 5')."

    )
    success_criteria:str=Field(
        description="A concrete, checkable condition for whether the experiment ran "
                    "correctly, independent of whether the hypothesis was confirmed."

    )
    compute_budget_seconds:int=Field(
        default=60,
        description="Maximum wall-clock time this experiment is allowed to run."

    )
    notes:Optional[str]=Field(
        default=None,
        description="Any additional context, caveats, or reasoning from the Planner."

    )

if __name__=="__main__":
    spec=ExperimentSpec(
        hypothesis="RMSNorm converges faster than LayerNorm on a tiny transformer.",
        task_description="Train a 2-layer transformer on a toy dataset for 100 steps "
                          "using RMSNorm, and print the final training loss.",
        expected_outcome="Final loss should be lower than a comparable LayerNorm run.",
        success_criteria="Script runs to completion and prints a single numeric loss value.",
    )
    print(spec.model_dump_json(indent=2))