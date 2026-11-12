"""Explainable, capacity-aware strategic decisions using V1 observations.

Offline, deterministic, non-causal. No LLM, scraping or external requests.
"""
from .creator_intelligence import analyze_creator
from .creator_strategy_contracts import (
    StrategyActionV2,
    StrategyBudgetV2,
    StrategyDecisionV2,
    StrategyRequestV2,
)

# These are editorial experiment templates, not empirically validated growth hacks.
_TEMPLATES: dict[str, dict[str, object]] = {
    "reduce_overload": {
        "title": "Protect a sustainable streaming schedule",
        "hypothesis": "A feasible schedule permits more consistent reporting.",
        "steps": [
            "Choose streaming slots that fit your actual weekly availability.",
            "Record streamed minutes and remaining production time for two weeks.",
            "Review the plan before adding new clip or content tasks.",
        ],
        "measurement": "Actual streamed hours compared with weekly hours available.",
        "evaluation_rule": "After two weeks, confirm that planned work fits the budget.",
        "minutes": 0,
    },
    "investigate_viewer_decline": {
        "title": "Compare like-for-like streams before changing the format",
        "hypothesis": "Some of the decline may relate to differences in stream conditions.",
        "steps": [
            "Select comparable stream dates, categories, durations and time slots.",
            "Document one change to test while keeping the others similar.",
            "Review weighted average viewers without assuming causation.",
        ],
        "measurement": "Average concurrent viewers for comparable streamed minutes.",
        "evaluation_rule": "Compare two follow-up weeks, noting uncertainty and any confounders.",
        "minutes": 40,
    },
    "start_clip_experiment": {
        "title": "Try a small, original short-form discovery experiment",
        "hypothesis": "A consistent clip routine may create additional discovery opportunities.",
        "steps": [
            "Choose one recorded stream moment that works without live-stream context.",
            "Create one short, clear clip with a strong opening and accurate description.",
            "Publish it and log results over a consistent observation window.",
        ],
        "measurement": "Clips published, comparable clip views, and optional new channel visits.",
        "evaluation_rule": (
            "Compare at least two clips over matched observation windows; "
            "do not infer causation or promise conversions."
        ),
        "minutes": 45,
    },
    "prepare_recordings": {
        "title": "Set up a viable recording and clip-review workflow first",
        "hypothesis": "Capturing your own content is a prerequisite to a repeatable clip routine.",
        "steps": [
            "Confirm that recordings and any other participants' voices can be used.",
            "Set up local capture or a supported platform recording workflow.",
            "Review one own recording and note a potential moment for a later clip.",
        ],
        "measurement": "Successful accessible recording and one documented candidate moment.",
        "evaluation_rule": "Confirm that recording and reuse work before scheduling publication.",
        "minutes": 20,
    },
    "review_clip_openings": {
        "title": "Examine why clip exposure might be changing",
        "hypothesis": "Different clip subjects or openings may partly explain varied reach.",
        "steps": [
            "Select clips of similar age, audience, subject and posting window.",
            "Compare the first seconds and context clarity without cherry-picking.",
            "Change one editorial choice and record the next comparison.",
        ],
        "measurement": "Comparable clip views and, if available, retention metrics.",
        "evaluation_rule": (
            "Review a minimum of two additional comparable clips; "
            "small samples are inconclusive."
        ),
        "minutes": 35,
    },
    "build_returner_habit": {
        "title": "Test a recognizable recurring stream segment",
        "hypothesis": "A clear recurring segment may help viewers recognize a reason to return.",
        "steps": [
            "Introduce one repeatable segment with a clear start and end.",
            "Keep its purpose and announcement consistent for two weeks.",
            "Compare weekly returning and unique viewers without assuming the segment caused change.",
        ],
        "measurement": "Weekly returning viewers alongside unique viewers.",
        "evaluation_rule": "Look for direction over several comparable weeks, not a guaranteed uplift.",
        "minutes": 30,
    },
    "clarify_follow_value": {
        "title": "Make the channel's value and next stream easy to understand",
        "hypothesis": "Clear information may reduce confusion for first-time visitors.",
        "steps": [
            "Explain what viewers can expect from the channel in one concise sentence.",
            "Publish a realistic next-stream schedule in an accessible place.",
            "Compare follows and unique viewers for similar weeks.",
        ],
        "measurement": "Weekly new follows relative to reported unique viewers.",
        "evaluation_rule": "Review two follow-up weeks; a change does not prove causation.",
        "minutes": 25,
    },
    "protect_successful_format": {
        "title": "Document repeatable elements of improving streams",
        "hypothesis": "Preserving what seems to work may reduce unnecessary experimentation.",
        "steps": [
            "List the segments, times and themes shared by recent streams.",
            "Keep one format consistent for two further weeks.",
            "Monitor weighted average viewers while recording major confounders.",
        ],
        "measurement": "Weighted average concurrent viewers at similar streaming times.",
        "evaluation_rule": "Check whether the descriptive increase persists, without predicting it.",
        "minutes": 20,
    },
    "collect_baseline": {
        "title": "Build a trustworthy baseline before making a growth change",
        "hypothesis": "Consistent measurements make later comparisons more meaningful.",
        "steps": [
            "Keep the current manageable stream routine.",
            "Record weekly streamed minutes, viewers and clips where available.",
            "Review the same definitions in two weeks before choosing an experiment.",
        ],
        "measurement": "Completeness and consistency of weekly creator-reported metrics.",
        "evaluation_rule": "Confirm two comparable weeks exist; do not interpret missing data as zero.",
        "minutes": 0,
    },
}

_SIGNAL_TO_ACTION = {
    "time_budget_overrun": "reduce_overload",
    "viewer_decline": "investigate_viewer_decline",
    "no_clips": "start_clip_experiment",
    "clip_reach_decline": "review_clip_openings",
    "returning_viewers_decline": "build_returner_habit",
    "follows_not_tracking_reach": "clarify_follow_value",
    "viewer_growth": "protect_successful_format",
    "baseline_review": "collect_baseline",
}


def _action_for_signal(signal: str, request: StrategyRequestV2) -> str:
    choice = _SIGNAL_TO_ACTION.get(signal, "collect_baseline")
    if choice == "start_clip_experiment" and not (
        request.has_own_recordings and request.can_edit_short_clips
    ):
        return "prepare_recordings"
    return choice


def _budget(request: StrategyRequestV2, experimental_minutes: int) -> StrategyBudgetV2 | None:
    total = round(request.weekly_hours_available * 60)
    minimum_stream = round(request.minimum_stream_hours * 60)
    # Reserve a small measurement window, but never pretend there is spare time.
    review = 15 if total - minimum_stream >= experimental_minutes + 15 else 0
    if total - minimum_stream < experimental_minutes + review:
        return None

    observed_hours = sum(w.stream_minutes for w in request.weeks[-2:]) / 120
    intended_stream = min(round(observed_hours * 60), total - experimental_minutes - review)
    intended_stream = max(intended_stream, minimum_stream)
    if intended_stream + experimental_minutes + review > total:
        return None

    return StrategyBudgetV2(
        available_minutes=total,
        streaming_minutes=intended_stream,
        experiment_minutes=experimental_minutes,
        measurement_minutes=review,
        unallocated_minutes=total - intended_stream - experimental_minutes - review,
    )


def _rank_signals(request: StrategyRequestV2, analysis) -> list[str]:
    """Honor hard capacity constraints, then put goal-relevant signals first.

    Severity outranks relevance: a medium goal-fit signal never beats a
    high-priority warning. Ties use editorial order, not an effectiveness claim.
    """
    goal_order = {
        "discovery": (
            "follows_not_tracking_reach",
            "clip_reach_decline",
            "viewer_growth",
            "returning_viewers_decline",
        ),
        "retention": (
            "returning_viewers_decline",
            "viewer_growth",
            "follows_not_tracking_reach",
            "clip_reach_decline",
        ),
        "consistency": (
            "viewer_growth",
            "returning_viewers_decline",
            "clip_reach_decline",
            "follows_not_tracking_reach",
        ),
    }
    preference = goal_order[request.primary_goal]
    severity = {"high": 0, "medium": 1, "low": 2}
    indexed = list(enumerate(analysis.insights))
    ranked = sorted(
        indexed,
        key=lambda row: (
            severity[row[1].priority],
            0 if row[1].code == "time_budget_overrun" else 1,
            preference.index(row[1].code) if row[1].code in preference else 99,
            row[0],
        ),
    )
    return [insight.code for _, insight in ranked]


def build_creator_strategy(request: StrategyRequestV2) -> StrategyDecisionV2:
    analysis = analyze_creator(request)
    signals = _rank_signals(request, analysis)
    chosen_signal = signals[0]
    chosen_code = _action_for_signal(chosen_signal, request)
    proposed = _TEMPLATES[chosen_code]
    minutes = int(proposed["minutes"])
    allocation = _budget(request, minutes)
    intervention_deferred = allocation is None

    if allocation is None:
        # With a protected minimum stream commitment, do not invent extra time.
        chosen_code = "collect_baseline"
        proposed = _TEMPLATES[chosen_code]
        minutes = 0
        allocation = _budget(request, minutes)
        assert allocation is not None  # validated minimum_stream_hours <= available hours

    prerequisite_notes: list[str] = []
    if chosen_code == "prepare_recordings":
        if not request.has_own_recordings:
            prerequisite_notes.append("Recordings are not yet available.")
        if not request.can_edit_short_clips:
            prerequisite_notes.append("An editing workflow has not been confirmed.")
        prerequisite_notes.append("Use only content you have permission to publish.")
    if chosen_code == "review_clip_openings" and not request.can_access_stream_summaries:
        prerequisite_notes.append("Detailed retention analytics are unavailable; use only clip counts.")

    if allocation.streaming_minutes < round(
        sum(w.stream_minutes for w in request.weeks[-2:]) / 2
    ):
        prerequisite_notes.append(
            "The proposed streaming minutes are lower than the recent weekly average "
            "to keep all work within available time."
        )

    if chosen_code == "collect_baseline" and chosen_signal != "baseline_review":
        prerequisite_notes.append(
            "No experiment fits the protected streaming commitment and available time. "
            "Reconsider the minimum hours or choose a lighter intervention."
        )

    signal = next(item for item in analysis.insights if item.code == chosen_signal)
    steps = list(proposed["steps"])
    if chosen_code == "prepare_recordings" and request.has_own_recordings:
        steps[1] = "Confirm a simple local editing method before trying to publish clips."
    evidence = signal.evidence_metrics if chosen_code != "collect_baseline" else [
        comparison.metric for comparison in analysis.comparisons
        if comparison.direction != "unavailable"
    ][:3]
    strategy = StrategyActionV2(
        code=chosen_code,
        title=str(proposed["title"]),
        reason=signal.observation,
        hypothesis=str(proposed["hypothesis"]),
        steps=steps,
        evidence=evidence,
        prerequisite_notes=prerequisite_notes,
        measurement=str(proposed["measurement"]),
        evaluation_rule=str(proposed["evaluation_rule"]),
        limitations=[
            "A short observational comparison cannot prove what caused an outcome.",
            "Targets are process checks, not promised audience or revenue growth.",
        ],
        extra_minutes_per_week=minutes,
    )
    return StrategyDecisionV2(
        strategy=strategy,
        budget=allocation,
        analysis=analysis,
        considered_signals=signals,
        deferred_signals=[
            code for code in signals
            if intervention_deferred or code != chosen_signal
        ],
        caveats=[
            "One experiment at a time; review after two comparable weeks.",
            "Creator-reported metrics have not been independently verified.",
            "No automatic connection, language model or paid API.",
        ],
    )
