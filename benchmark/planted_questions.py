from pydantic import BaseModel, Field
from typing import Literal

class PlantedQuestion(BaseModel):
    id: str = Field(description="Short, stable identifier, e.g. 'lr_divergence_01'.")
    research_question: str = Field(
        description="Phrased exactly as it would be handed to the pipeline -- "
                    "no hints toward the answer."
    )
    ground_truth_verdict: Literal["supports", "refutes"] = Field(
        description="What a correct Analyst verdict should be, given the hypothesis "
                    "Planner is expected to generate for this question."
    )
    ground_truth_justification: str = Field(
        description="Why we're confident in this answer -- textbook fact, prior "
                    "verified run, or well-established theory. Must be checkable "
                    "by a human independent of the pipeline's own output."
    )
    mechanism: str = Field(
        description="Short tag for what ML concept this tests, e.g. 'learning_rate', "
                    "'regularization', 'batch_size' -- used to ensure benchmark "
                    "coverage isn't accidentally lopsided."
    )

PLANTED_QUESTIONS = [
    PlantedQuestion(
        id="lr_divergence_01",
        research_question=(
            "Does using an extremely high learning rate (100x higher than a "
            "well-tuned value) cause SGD to diverge rather than converge, "
            "compared to a well-tuned learning rate, when training a simple "
            "linear regression model on synthetic data?"
        ),
        ground_truth_verdict="supports",
        ground_truth_justification=(
            "Well-established result in optimization theory: for gradient descent "
            "on a convex quadratic loss (linear regression's MSE), there is a "
            "theoretical maximum stable learning rate related to the largest "
            "eigenvalue of the Hessian / feature covariance matrix. A learning "
            "rate 100x above a well-tuned value will overshoot this stability "
            "bound, causing loss to oscillate with increasing amplitude or diverge "
            "to infinity/NaN, rather than decrease. This is textbook convex "
            "optimization, not something requiring a novel experiment to establish -- "
            "we're testing whether Kepler's pipeline can correctly discover and "
            "verify a well-known result end-to-end."
        ),
        mechanism="learning_rate",
    ),
]