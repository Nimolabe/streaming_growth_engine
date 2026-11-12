# Clip Intelligence — Review Quality V3

This is a backward-compatible reliability pass on the existing offline clip
reference benchmark, built from `feature/clip-reference-benchmark-v1`.
**It does not download Twitch/YouTube media or claim semantic video recognition.**

## Problem discovered during review

The previous reviewer-consensus function matched every reviewer separately
against the first reviewer, accepting all matches within a tolerance. That
could produce a false "consensus": timestamps at 7 s, 10 s and 13 s all
match the 10 s anchor within 3 s, but the actual reviewer spread is **6 s**.

V3 only accepts a highlight if:
1. Every reviewer identifies the same number of highlights.
2. Labels match one-to-one against the anchor within the stated tolerance.
3. The **full minimum-to-maximum spread across every reviewer** is within
   the tolerance.
4. Consensus rounding does not collapse distinct timestamps.

Conflicting sets stay in `reviewer_disagreement` and **never contribute**
to performance denominators.

## Real-world metrics separated from synthetic tests

Earlier aggregated results included synthetic cases, which can be useful for
software tests but must **never** be presented as field performance. The API
now exposes additional fields:

- `synthetic_cases`: deliberately artificial examples
- `real_reviewed_cases`: cases marked as watched by independent reviewers
- `real_reviewed_eligible_cases`: watched cases where labels agree
- `real_reviewed_precision` and `real_reviewed_recall`: metrics computed
  **only from eligible, direct-human-viewing cases**

Both real metrics are `null` when their denominator is absent. The legacy
`overall_precision`/`overall_recall` fields remain to avoid breaking
clients but may include synthetic cases; don't present them as real-world
quality. The source's asserted review flag is not independently authenticated:
the caller must document how the review happened.

## More useful clip categories

`content_category` is optional in existing requests (default `unknown`).
Allowed labels: `gameplay`, `conversation`, `reaction`, `irl`,
`other`, `unknown`. The label is preserved for each case in the response.
These are **manual input labels**, not features inferred by the scanner.

## Limitations and next verification

- Human labels can be biased; held-out recording sessions, separate creator
  groups, and both non-highlight and highlight segments are essential.
- Timing agreement alone does not establish creative quality or commercial
  performance. No causal "growth" claims are supported.
- This phase does not include any rights-cleared real Twitch or YouTube
  recordings or real case annotations.
- Regression tests cover strict reviewer spread, disagreement exclusions,
  category validation and synthetic-vs-real metric separation.
- CI runs Python/pytest and Ruff; if FFmpeg-dependent tests are skipped,
  their absence must remain visible.
- Leave the website and `main` unchanged; use a draft PR.

## Blind review queue — new local endpoint

`POST /api/v1/clips/review-queue` accepts an existing
`ClipReviewResultV2` in the `scan` field. This endpoint **never opens or
retrieves media**. It returns timestamp ranges for independent review:

- Existing scanner candidates (not guaranteed highlights).
- Up to ten deliberately **unflagged** comparison intervals selected from
  available recording time outside candidates with a configurable margin.
- Deterministic opaque task IDs and tasks sorted by ID, without cue labels,
  prediction scores or control flags in individual reviewer-facing tasks.
- A count of requested control intervals that cannot safely fit.

Example: a 120-second scan with audio peaks at 20 s and 90 s may generate two
candidate tasks and up to three additional, non-overlapping control tasks.
The person running the review must provide access to the source through an
**authorized** playback method and keep task origin/agent scores hidden from
reviewers. The counts in the response are administrator metadata, so share
only `tasks` and `reviewer_instructions` with blinded reviewers.

A comparison interval is not a known negative. Reviewers should label
**yes/no/uncertain**, content type and needed context in their own words,
then resolve disagreements before estimating precision and recall.
The queue cannot prove clip quality, legality or publication rights and does
not perform automatic video watching or semantic analysis.

Synthetic tests check reproducibility, timeline bounds, blind task fields,
non-overlapping comparison windows and API input validation.
