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


## 2026-08-08 — Grounding check over-rejects real quotes (formatting-sensitive)

Stress-tested check_grounding() (added today, see analyst_agent.py) with
synthetic but realistic variants of a real output line -- not hallucinations,
just formatting differences an LLM plausibly introduces when copying:

  exact match (control)               -> grounded=True
  trailing period added               -> grounded=False
  line-break normalized to space      -> grounded=False
  number reformatted (0.570)          -> grounded=False
  trailing % added                    -> grounded=False
  extra whitespace collapsed          -> grounded=False

Why it matters: check_grounding() uses strict `quote_clean in output`
substring containment. This means it will downgrade genuinely correct,
real evidence to "inconclusive" any time the LLM's copy isn't byte-exact
-- which based on this test is most of the time, not rarely. The fix we
shipped today for the hallucination bug (#11) risks trading a rare false
positive (invented quote) for a common false negative (real quote,
rejected). Not yet measured how often this fires in live runs -- next
step is running this against real Analyst outputs, not just synthetic
cases.

Real fix is probably NOT more string-munging (strip trailing punctuation,
normalize whitespace, etc.) added ad hoc -- that's a losing game against
open-ended reformatting. Worth discussing: fuzzy/normalized match with a
documented normalization spec (lowercase, collapse whitespace, strip
terminal punctuation only) vs. a small edit-distance tolerance vs.
requiring the LLM to quote a full line/sentence instead of an arbitrary
span. Filed as issue -- see below.


## 2026-08-08 — Fixed grounding over-rejection (see #12)

Added _normalize_for_grounding() to check_grounding(): lowercase, collapse
all whitespace/newlines to a single space, strip a small explicit set of
trailing punctuation (. , %) from the quote before substring comparison.

Re-ran tests/test_grounding_batchA.py after the fix:

  exact match (control)               -> grounded=True
  trailing period added               -> grounded=True   (was False)
  line-break normalized to space      -> grounded=True   (was False)
  number reformatted (0.570)          -> grounded=False  (unchanged, on purpose)
  trailing % added                    -> grounded=True   (was False)
  extra whitespace collapsed          -> grounded=True   (was False)

Deliberately left numeric-formatting differences (0.57 vs 0.570) as
NOT grounded. Normalizing numbers risks masking a real discrepancy
between what the LLM claims and what the output actually says --
chose to keep failing safe (reject real evidence) over failing open
(let numeric fuzziness through). This is a live tradeoff, not settled --
worth revisiting if it turns out to reject a meaningful fraction of
real Analyst outputs once we run against live data instead of synthetic
cases.

Re-ran the original hallucination-check smoke test (agents/analyst/analyst_agent.py
__main__ block) after the fix -- verdict/grounding unchanged, confirms
normalization didn't loosen the check enough to let a fabricated quote
through.

Still TODO: check_grounding() proves a quote is real, not that it
supports the claimed verdict (see #12 discussion) -- this is Batch B,
not yet run.


## 2026-08-08 — Batch B: grounded quote, wrong verdict (real bug, see new issue)

Tested whether a correctly-grounded (verbatim, real) quote guarantees a
correct verdict. It does not. Ran the same B1 case (tests/test_grounding_batchB.py,
adversarial robustness example, real answer is "refutes": 0.89 < 0.91) 5 times:

  run 1: refutes  (correct)
  run 2: supports (WRONG -- same exact quote as the others, "0.89 compared
                    to 0.91" reasoned as "higher"/"more robust" -- simple
                    comparison error, not a fabrication)
  run 3: refutes  (correct)
  run 4: refutes  (correct)
  run 5: refutes  (correct)

check_grounding() passed run 2 without complaint -- the quote IS real and
verbatim, identical to the quote used in the 4 correct runs. This confirms
the gap flagged when #11 was left open: grounding proves a quote is real,
not that the reasoning built on it is sound. A backwards numeric comparison
slips through completely undetected by the current pipeline.

Sample size is small (n=5, one case) -- not claiming a rate, just confirming
the failure mode exists and is reproducible in kind. Next: run more trials
and/or more distinct cases to get a sense of frequency before deciding how
urgent a fix is.

check_grounding() cannot catch this by design -- it's a substring check,
not a logic check. Would need something structurally different: e.g. a
secondary self-consistency pass, extracting the compared numbers
programmatically and checking the verdict direction matches, or a second
LLM pass specifically asked to verify the arithmetic/comparison in the
reasoning against the quote.

## 2026-08-08 (cont.) — B2: cherry-picking confirms same failure class as #13

Added B2 to tests/test_grounding_batchB.py: multi-seed data (5 seeds,
4/5 show new_optimizer worse than baseline, mean confirms refutes).
5 trials: 4/5 reasonable (refutes/inconclusive, cited the mean). 1/5
cherry-picked Seed 3 alone (real quote, passes check_grounding) and
generalized to "consistently... across all seeds" -- false.

Combined with B1 (10 trials, 7 correct/3 wrong), same underlying bug
confirmed via a second, distinct mechanism. Filed as a comment on #13
rather than a new issue -- same root cause (grounded quote != sound
reasoning), just a second manifestation. Rough combined rate ~4/15
(~27%) wrong across both scenarios -- small-n, not rigorous, but high
enough to not dismiss as a fluke.

Not fixed today. Directions discussed in #13 (programmatic comparison
extraction, second verification pass, majority-vote sampling) apply
to both mechanisms since the root cause is the same. Good next-session
starting point: given how central this is to Milestone 4 (the whole
benchmark's value depends on trusting Analyst verdicts), this probably
deserves being tackled properly rather than patched further."

## 2026-08-09 — Fixed double sandbox execution in run_with_self_correction

Found while starting on budget/cost tracking: run_with_self_correction had
an unconditional `sandbox_result = run_code_in_sandbox(...)` call sitting
right after the if/else that was supposed to choose between a syntax-check
failure and a real sandbox run. Two real consequences:

1. The syntax-check skip never actually worked -- even on invalid code,
   the sandbox still ran afterward and silently overwrote the syntax
   failure result.
2. Every successful attempt ran the generated code in the sandbox TWICE --
   doubling real compute cost per attempt for no reason.

Deleted the duplicate line. Added tests/test_run_loop_sandbox_calls.py
(mocks generate_code/run_code_in_sandbox/basic_sanity_check to isolate
control flow) confirming: syntax failure -> 0 sandbox calls (was
previously 1, defeating the skip); valid syntax -> 1 sandbox call
(was previously 2).

Relevant context: this was caught specifically because we were about to
build cost/budget tracking on top of this function -- would have been
tracking double the real cost per attempt if we hadn't caught it first.