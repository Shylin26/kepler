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

## 2026-08-09 — Cost/duration tracking wired end-to-end

Added real wall-clock duration tracking, from the sandbox up through the
knowledge graph:

- execution/sandbox/executor.py: run_code_in_sandbox now measures actual
  container run time (time.monotonic(), around container.wait()) and
  returns it as duration_seconds. Verified against a real Docker call
  with a deliberate time.sleep(2) -- measured 2.289s, plausible.
- run_loop.py: run_with_self_correction sums duration_seconds across all
  attempts into total_sandbox_seconds (uses .get(..., 0) since a
  syntax-check-failure attempt never touches the sandbox and has no
  duration_seconds key at all).
- memory/trajectory_store/logger.py: persists total_sandbox_seconds and
  the original compute_budget_seconds side by side in the trajectory JSON.
- memory/knowledge_graph/graph_client.py: log_run_to_graph gained a new
  total_sandbox_seconds parameter (default 0.0, backward compatible),
  written onto the Run node so it's queryable directly from Cypher.

Verified end-to-end with a real python run_loop.py pipeline run (Director
-> Planner -> 3x Ray-parallel experiments -> graph). Confirmed via Cypher
query against the exact Run node IDs from that run:
  Run :46 -- 3 attempts, failed -- 0.767s
  Run :47 -- 3 attempts, failed -- 2.405s
  Run :48 -- 3 attempts, failed -- 1.015s

Minor note for future self: first verification attempt gave false NULLs
-- turned out to be two separate causes, not one. (1) queried before the
new pipeline run had actually executed, so pulled pre-fix nodes. (2) even
after re-running, ORDER BY elementId(r) DESC sorts elementId as a STRING,
not numerically -- so it surfaced old single/double-digit-suffix nodes
instead of the new ones. Fixed by querying exact known IDs instead of
trusting sort order. Worth remembering for any future Neo4j debugging:
elementId is not safe to sort on numerically.

Still not done: nothing currently compares total_sandbox_seconds against
spec.compute_budget_seconds to flag/act on overruns -- this only tracks
spend, doesn't enforce or alert on it yet. Also doesn't yet track LLM
API/token cost, only sandbox wall-clock time. Both reasonable next steps
if we come back to budget tracking.


## 2026-08-11 — budget_exceeded flag added (tracking, not enforcement)

Investigated whether compute_budget_seconds is a per-attempt or total
budget. Turns out it's passed as the Docker timeout on EVERY attempt in
run_with_self_correction -- so a 3-attempt retry loop can legitimately
use up to 3x the nominal budget in total sandbox time, with nothing
flagging it. Per-attempt overrun can't actually happen (Docker's own
container.wait(timeout=...) kills it), but total-loop overrun was
completely invisible until today.

Decided (with human) not to change the semantics or add enforcement yet
-- real trajectory data from 6 runs showed budget usage well under 100%
(1-37%) in every real case so far, so there's no evidence yet that this
is an active problem, just an unguarded gap. Chose to make it visible
first: added budget_exceeded (bool) to run_with_self_correction's return
dict, computed as total_sandbox_seconds > spec.compute_budget_seconds,
printed as a warning and persisted through trajectory JSON + Neo4j Run
node (same pattern as total_sandbox_seconds).

Also discovered ExperimentSpec.compute_budget_seconds is validated as
int, not float (Pydantic rejects fractional budgets) -- minimum
granularity is 1 second.

Verified with a real forcing test (tests/test_budget_exceeded_flag.py):
mocked Coder (fixed code with a real 0.5s sleep) and Critic (forced
failure, exhausts all 3 attempts) but NOT the sandbox itself -- real
Docker calls. 3 attempts x ~0.55-0.65s genuine duration summed to
1.73-1.79s against a 1s budget -- correctly flagged budget_exceeded=True,
confirmed via the WARNING print and the return dict.

Still not done: nothing stops or alters behavior when budget_exceeded
is True -- purely observational for now. Also still missing: LLM/token
cost tracking (separate from sandbox time). See issue for both.


## 2026-08-12 — check_numeric_direction() added to Analyst (partial #13 fix)

Built a narrow heuristic to catch the exact failure pattern found in #13's
B1 stress test: reasoning that cites two numbers with a directional word
(higher/lower/more/less/etc.) where the claimed direction contradicts the
actual arithmetic. Deliberately NOT a general logic checker -- doesn't
touch cherry-picking (B2) and can't resolve reasoning that uses both
direction-word types in the same sentence (confirmed this limitation is
real, not hypothetical -- tested directly against the self-contradictory
run from the original B1 batch, correctly returns checked=False,
"ambiguous, skipping" rather than a false catch).

Validated against real reasoning strings from yesterday's B1 stress test
before wiring into analyze_result: 5/5 correct (caught the one known-bad
run, zero false positives on the four good ones).

Integration: flag-only, same philosophy as budget_exceeded from earlier
this week -- does NOT override the verdict. direction_check is now a
field in analyze_result()'s return dict (checked/consistent/reason).
Deliberately chose not to match check_grounding's auto-downgrade pattern,
since this is a heuristic with known blind spots (n=6 validated cases is
small), not a deterministic substring check -- didn't want to risk a new
failure mode (false-positive downgrades) while fixing an old one.

Real mid-session mistake worth recording: first implementation attempt
used the auto-downgrade pattern despite deciding against it -- an earlier
draft got pasted into the file and the revised flag-only version never
actually replaced it. Caught because the live re-test showed
direction_check missing entirely from every real output; grep'd the file
directly instead of assuming the edit had landed, found the stale
downgrade-style code still present, fixed it properly, re-verified.
Lesson: always grep/view the actual file state after an edit before
re-running an expensive test batch, don't assume the edit instructions
were applied correctly just because they were sent.

Still not done: still doesn't catch cherry-picking (B2), still don't have
a large-n false-positive rate for check_numeric_direction on real (not
synthetic) Analyst outputs across varied hypotheses -- only tested on the
adversarial-training example so far. Good next step: run this against a
wider variety of real experiment outputs before considering whether to
someday move it from flag-only to enforcement."


## 2026-08-12 (cont.) — confirmed second blind spot in check_numeric_direction

Tested check_numeric_direction() against real B2 cherry-picking reasoning
("consistently reaches target loss in fewer steps... across all seeds" --
the false generalization from yesterday's B2 run 3). Result: checked=False,
"Fewer than 2 numbers found in reasoning" -- confirmed, cherry-picked
generalizations often cite NO numbers at all, so there's nothing for this
heuristic to even attempt to check.

This is a distinct blind spot from the mixed-direction-language one found
earlier today -- not the same limitation restated. Two known gaps now:
(1) reasoning using both higher/lower-type words in one sentence -> ambiguous,
skipped. (2) reasoning with a false claim but zero cited numbers -> nothing
to check at all. #13's B2 mechanism (cherry-picking) remains fully uncaught
by anything shipped so far -- would need something structurally different,
e.g. checking whether the quote represents the full/majority of relevant
data points rather than one favorable outlier.

## 2026-08-12 (cont.) — check_generalization_scope() added (B2 mechanism, #13)

Built check_generalization_scope(reasoning, quote, output): flags when
reasoning uses universal language (consistently/across all/every case/
etc.) but the quoted evidence is only 1 of several structurally similar
lines in the real output (matches lines by replacing all numbers with a
placeholder and comparing templates -- works for any repeated-per-sample
output format, not hardcoded to seeds).

Tested against real B2 data (tests/test_generalization_scope.py):
- Real cherry-pick (Seed 3 of 5, "consistently...across all seeds") ->
  correctly flagged, possible_cherry_pick=True, sibling_count=5.
- Honest run (cites the Mean line, no universal language) -> correctly
  not flagged (nothing to check).
- Adversarial control: a TRUE universal claim, but only the Mean line
  quoted -> correctly returned checked=False, "no structurally similar
  siblings" -- because Mean has no template-siblings among the Seed
  lines. This is a real, explainable scope limit (the check has no
  opinion on summary-statistic-only citations), not a bug.

Wired into analyze_result() as a flag only (generalization_check field),
same philosophy as direction_check and budget_exceeded -- does not
override the verdict.

Real mid-session mistakes, caught before committing (worth recording,
this is the second time in two days this exact class of mistake
happened -- pattern worth noting for next time):
1. Test file was missing its import line entirely (copy/paste gap) --
   caused a confusing NameError instead of an ImportError. Diagnosed by
   testing the import in isolation rather than assuming the function
   was broken.
2. The wiring edit landed OUTSIDE analyze_result's try/except entirely
   (after the except block), with broken indentation -- unreachable,
   and should have been a SyntaxError. Diagnosed with grep + sed to see
   real file content, confirmed with ast.parse before running anything
   expensive, then replaced the whole broken region cleanly in one shot
   instead of patching further.

Lesson reinforced: multi-line pasted edits into an existing function are
fragile via this workflow -- worth grep/sed-confirming the actual file
state immediately after any such edit, every time, not just when
something looks wrong afterward.

Still not done: check_generalization_scope only catches cherry-picking
when there ARE multiple structurally similar lines to compare against
and universal language is used -- doesn't help when the false claim is
phrased without universal words, or when the output format doesn't have
repeated structurally-identical lines. #13 can probably be considered
"reasonably mitigated for the two mechanisms we found" at this point,
not "solved" -- no general guarantee against Analyst reasoning errors.

## 2026-08-12 (cont.) — edge-case coverage for check_generalization_scope

Added empty-input edge cases to tests/test_generalization_scope.py:
empty reasoning+quote, and universal language with no quote at all.
Both behave correctly -- no crashes, checked=False with a sensible
reason each time (no universal language found / no quote to compare
against). No further action needed, just closing the gap between this
function and check_numeric_direction, which already had equivalent
edge-case coverage.

## 2026-08-13 — confirmed check_generalization_scope generalizes across output formats

Tested check_generalization_scope against epoch-based logs ("Epoch N:
loss=X") instead of the original seed-based format it was built
against -- different label word, different metric name, same
structural shape (5 similar lines). Correctly flagged a cherry-picked
epoch cited with universal language, correctly stayed silent on an
honest non-universal claim. Confirms the digit-templating approach
generalizes structurally rather than being accidentally tuned to the
one example (Seed-N) it was designed against.


## 2026-08-13 (cont.) — key finding: generalization flag can't tell true from false

Tested whether check_generalization_scope distinguishes a TRUE universal
claim (all 5 seeds genuinely agree, new_optimizer faster in every one)
from a FALSE one (the original B2 bug, 4/5 seeds actually disagree) when
both only cite one seed as evidence. Result: IDENTICAL output in both
cases -- possible_cherry_pick=True, same reason text, same sibling_count.

This confirms precisely what the function actually measures: citation
completeness (did the Analyst demonstrate checking all comparable data),
NOT correctness of the claim itself. It would have caught the real B2
bug, but it will equally flag perfectly true conclusions that just
didn't cite every line. Important for any future decision about
enforcement -- auto-downgrading on this flag would penalize correct
reasoning about as often as incorrect reasoning. Reinforces the earlier
decision to keep this (and direction_check, budget_exceeded) flag-only.

Also: while consolidating all of today's test cases into one clean file
(after several rounds of malformed edits -- see below), found and fixed
a real bug in the test harness itself: the epoch-based test cases were
being evaluated against real_output (the seed data) instead of
epoch_output, meaning the earlier "epoch generalizes across formats"
result, while directionally correct in its conclusion, was actually
being computed against the wrong data the whole time. Re-ran after the
fix -- same correct result, but now actually testing what it claims to
test.

Process note: several edits today went in with literal placeholder text
("...existing cases...") mistakenly typed in verbatim instead of the
real content it stood in for -- caused repeated SyntaxErrors. Fixed by
abandoning incremental patches and writing one complete, correct file
in a single pass instead. Lesson: for multi-section file edits via this
workflow, a full-file rewrite is often safer than several sequential
partial edits, especially once a file has drifted from a known-good
state."

## 2026-08-14 — real-world confirmation: check_grounding caught a live digit transcription error

During a real python run_loop.py pipeline run, the Analyst produced this
reasoning: "The momentum method shows a higher error and more erratic
convergence compared to vanilla gradient descent," quoting:
  "Step 2 (Momentum): theta_0 = 1.9278508718468521, theta_1 = ..."

The REAL sandbox output for that line was:
  "Step 2 (Momentum): theta_0 = 0.9278508718468521, theta_1 = ..."

Single leading-digit transcription error (0 -> 1), everything else
identical. check_grounding correctly rejected this as not grounded
(even after #12's normalization fix, since normalization deliberately
never touches numeric digits) and downgraded the verdict to
inconclusive.

This is the first live, non-synthetic confirmation of check_grounding
working as intended, and it specifically validates the #12 decision to
NOT normalize numeric formatting -- a looser numeric-normalization
scheme could plausibly have treated 1.927... and 0.927... as "close
enough" and let a real transcription error through as grounded.

Also confirmed (not a bug): direction_check and generalization_check
never ran on this response, since check_grounding's early-return on
failure happens before either check executes in analyze_result(). No
point checking the direction/scope of an already-fabricated quote --
correct short-circuit behavior."

## 2026-08-20 (cont.) — confirmed direction_check and generalization_check work together

Tested check_numeric_direction and check_generalization_scope against a
single reasoning string designed to trip both (backwards comparison +
cherry-picked universal claim). Both fired independently and correctly,
no interference between them. See tests/test_checks_together.py.

Also added a permanent regression test (tests/test_grounding_real_world_case.py)
locking in the real digit-transcription bug caught live today during an
actual pipeline run (1.927... misquoted for 0.927...) -- first live,
non-synthetic confirmation that check_grounding works as intended, and
specific validation of the earlier #12 decision not to normalize numeric
formatting.

Stepping away from Kepler for a bit to focus on internship interview
prep. Nothing left in a broken state -- #13 has real, honest, tested
progress (both known mechanisms mitigated, limits clearly documented),
all commits pushed, NOTES.md current.

## 2026-08-20 (cont. 2) — stress-tested check_syntax() edge cases

Tested check_syntax() (Coder agent, used in run_loop.py's retry loop)
against two previously-untested edge cases it could plausibly choke on:
null bytes in source code, and deeply nested parentheses (5000 levels).
Both handled gracefully -- CPython's compile() raises SyntaxError for
both cases (not ValueError/RecursionError as guessed going in), and
check_syntax's existing `except SyntaxError` correctly catches both.
No uncaught crash risk found from these two cases specifically.

Not proof no input can crash it -- just rules out the two most
plausible-looking edge cases. See tests/test_check_syntax.py.

Stepping away from Kepler to focus on internship interview prep.
Nothing left broken or half-done -- see previous NOTES entry today for
full status.