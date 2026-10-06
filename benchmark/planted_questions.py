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
    PlantedQuestion(
        id="l2_weight_shrinkage_01",
        research_question=(
            "Does adding L2 regularization reduce the magnitude of learned "
            "weights compared to training without regularization, on a simple "
            "linear regression task with the same data and number of training "
            "steps?"
        ),
        ground_truth_verdict="supports",
        ground_truth_justification=(
            "Definitionally true by how L2 regularization is constructed: it adds "
            "lambda * ||w||^2 to the loss function, directly penalizing weight "
            "magnitude during optimization. This isn't an empirical question with "
            "room for surprise -- it follows directly from the loss function's "
            "mathematical definition. A correct pipeline should reliably confirm "
            "this; failure here would indicate a problem with Coder's "
            "implementation or Analyst's measurement, not genuine ambiguity in "
            "the underlying science."
        ),
        mechanism="regularization",
    ),
    PlantedQuestion(
        id="batch_size_gradient_variance_01",
        research_question=(
            "Does using a larger batch size reduce the variance of gradient "
            "estimates (and therefore produce smoother, less noisy loss curves) "
            "compared to a smaller batch size, when training a model on the same "
            "synthetic dataset?"
        ),
        ground_truth_verdict="supports",
        ground_truth_justification=(
            "Standard statistical fact: under typical i.i.d. sampling assumptions, "
            "the variance of a mini-batch gradient estimate scales as "
            "1/batch_size. Averaging over more samples per step reduces estimate "
            "noise. This is textbook statistics (law of large numbers applied to "
            "gradient estimation), not a subtle or contested empirical claim."
        ),
        mechanism="batch_size",
    ),
    PlantedQuestion(
        id="epochs_always_improve_01",
        research_question=(
            "Does increasing the number of training epochs always decrease final "
            "training loss, with no risk of overfitting or instability, on a "
            "simple linear regression task?"
        ),
        ground_truth_verdict="refutes",
        ground_truth_justification=(
            "Deliberately planted as a FALSE hypothesis to test whether the "
            "pipeline can correctly push back rather than confirm everything "
            "presented to it. The claim's strong, unqualified language ('always', "
            "'no risk') is false: training loss can plateau once convergence is "
            "reached (further epochs yield negligible improvement, not continued "
            "decrease), and numerical instability or oscillation is possible "
            "depending on the optimization setup. A well-functioning Analyst "
            "should refute this overclaim rather than confirm it. This question "
            "exists specifically to catch a pipeline that rubber-stamps "
            "hypotheses as true regardless of their actual soundness."
        ),
        mechanism="training_dynamics",
    ),
    PlantedQuestion(
        id="zero_init_symmetry_01",
        research_question=(
            "Does initializing all weights to zero (instead of small random "
            "values) prevent a simple 2-layer neural network from learning "
            "effectively, due to symmetric gradients?"
        ),
        ground_truth_verdict="supports",
        ground_truth_justification=(
            "Classic, well-documented neural network pathology taught in every "
            "introductory deep learning course: zero-initializing all weights in "
            "a layer causes every neuron to compute identical outputs and receive "
            "identical gradients during backpropagation, so they remain "
            "symmetric and effectively identical throughout training -- the "
            "network fails to learn diverse features. This is established "
            "theory, not something requiring a novel experiment to discover."
        ),
        mechanism="weight_initialization",
    ),
]