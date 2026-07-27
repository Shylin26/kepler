# Kepler — Known Limitations & Open Issues

## LLM-as-judge inconsistency in task_adherence_check (found Day 1)

The `task_adherence_check` Critic layer gives **different verdicts on the same
underlying behavior** depending on the run:

- It correctly rejected a "silent task-cheat" (changing `-` to `+` in a divisor
  to dodge a division-by-zero) in one run.
- It then approved the *exact same kind of cheat* in a later run.
- Separately, it once rejected a *correct* graceful-error-handling attempt,
  giving a technically-true-but-irrelevant reason (pointing out the division
  is zero, when the task explicitly wanted that zero-division to be caught
  and reported).

Root cause: a single LLM judge call is stochastic and doesn't reliably apply
a consistent standard across runs, especially on a small 7B local model.

### Why this matters
This is not a bug to "just fix" — it's the central unsolved problem this whole
project is built around (see design doc, Section 12: Evaluation Methodology,
and Section 17: Failure Modes — "Reward hacking the Critic"). A Critic that
can be gamed, or that flip-flops on the same input, cannot be trusted as a
ground-truth signal for fine-tuning later (Milestone 5) — it would teach the
Coder Agent inconsistent lessons about what counts as "success."

### Real fix (deferred to Milestone 4 — Verification & Eval Harness)
- Sample the judge multiple times per verdict and use majority vote, not a
  single call.
- Build the "planted-answer" benchmark (Section 12) so judge behavior can be
  measured against known-correct verdicts, not just eyeballed.
- Periodically hand-check a sample of judge verdicts against my own judgment
  (inter-rater reliability), the same way the MT-Bench paper validates its
  LLM judges against human preference.
- Consider a stricter judge prompt that explicitly separates "did an error
  occur" from "was the error handled as instructed" — cheap partial mitigation,
  not a full fix.

### Status: open, deferred intentionally. Not blocking further milestones,
but must be revisited before any fine-tuning happens on Critic-labeled data.