"""Conservative, fully offline creator intelligence engine.

All metrics are supplied by the user; no scraping, account connections, or LLM.
"""
from statistics import mean

from .creator_intelligence_contracts import (
    CreatorInsight,
    CreatorIntelligenceRequest,
    CreatorIntelligenceResponse,
    MetricComparison,
    WeeklyMetrics,
)

_FIELDS = ("stream_minutes", "average_viewers", "unique_viewers",
           "follows", "returning_viewers", "clips_published", "clip_views")


def _period_value(weeks: list[WeeklyMetrics], field: str) -> float | None:
    # Never extrapolate from absent data or partially populated reporting periods.
    values = [getattr(week, field) for week in weeks]
    if any(value is None for value in values):
        return None
    if field == "average_viewers":
        weights = [week.stream_minutes for week in weeks]
        if sum(weights) == 0:
            return None
        return round(sum(value * weight for value, weight in zip(values, weights))
                     / sum(weights), 2)
    if field == "stream_minutes":
        return round(sum(values) / len(values) / 60, 2)  # weekly hours
    if field in {"unique_viewers", "returning_viewers", "follows", "clip_views",
                 "clips_published"}:
        return float(sum(values))  # total per half of the observation window
    return round(mean(values), 2)


def _comparison(weeks: list[WeeklyMetrics], field: str) -> MetricComparison:
    mid = len(weeks) // 2
    earlier = _period_value(weeks[:mid], field)
    recent = _period_value(weeks[mid:], field)
    note = "First half versus second half of consecutive weeks."
    if field == "stream_minutes":
        note += " Values are average streamed hours per week."
    elif field == "average_viewers":
        note += " Values are weighted by stream minutes, not summed."
    else:
        note += " Values are period totals; unequal half lengths are normalized."
    # Odd-sized series: normalize totals to a common weekly rate before comparing.
    if field not in {"stream_minutes", "average_viewers"}:
        if earlier is not None:
            earlier = round(earlier / mid, 2)
        if recent is not None:
            recent = round(recent / (len(weeks) - mid), 2)
        note = note.replace("period totals", "average weekly counts")
    if earlier is None or recent is None:
        return MetricComparison(metric=field, earlier=earlier, recent=recent,
                                change_percent=None, direction="unavailable",
                                note=note + " Incomplete data; cannot compare.")
    if earlier == 0:
        if recent == 0:
            return MetricComparison(metric=field, earlier=earlier, recent=recent,
                                    change_percent=0, direction="flat", note=note)
        return MetricComparison(metric=field, earlier=earlier, recent=recent,
                                change_percent=None, direction="up",
                                note=note + " Percent growth from zero is undefined.")
    delta = round((recent - earlier) / earlier * 100, 1)
    direction = "up" if delta > 5 else ("down" if delta < -5 else "flat")
    return MetricComparison(metric=field, earlier=earlier, recent=recent,
                            change_percent=delta, direction=direction, note=note)


def _insight(code: str, priority: str, observation: str, action: str,
             verify: str, evidence: list[str], *, cautious: bool = True) -> CreatorInsight:
    return CreatorInsight(
        code=code, priority=priority, observation=observation,
        interpretation=(
            "This is a descriptive signal, not proof of the underlying cause."
            if cautious else
            "This is an observed reporting pattern, not a growth guarantee."
        ),
        action=action, verification=verify, evidence_metrics=evidence,
        confidence="limited" if cautious else "moderate",
    )


def analyze_creator(data: CreatorIntelligenceRequest) -> CreatorIntelligenceResponse:
    weeks = data.weeks
    comparisons = [_comparison(weeks, name) for name in _FIELDS]
    comp = {c.metric: c for c in comparisons}
    missing = [
        field for field in _FIELDS
        if any(getattr(week, field) is None for week in weeks)
    ]
    notes: list[str] = []
    if any(w.stream_minutes == 0 for w in weeks):
        notes.append("At least one week has no stream time; avoid interpreting it as retention loss.")
    if len(weeks) < 8:
        notes.append("Fewer than eight weeks: changes may reflect ordinary variation.")
    if "unique_viewers" in missing or "returning_viewers" in missing:
        notes.append("Retention cannot be evaluated reliably without both unique and returning viewers.")
    if "clip_views" in missing or "clips_published" in missing:
        notes.append("Clip reach cannot be compared reliably without consistent clip reporting.")

    insights: list[CreatorInsight] = []
    streamed = comp["stream_minutes"]
    viewers = comp["average_viewers"]
    unique = comp["unique_viewers"]
    follows = comp["follows"]
    clips = comp["clips_published"]
    clip_views = comp["clip_views"]
    returning = comp["returning_viewers"]

    recent_hours = streamed.recent
    if recent_hours is not None and recent_hours > data.weekly_hours_available * 1.15:
        insights.append(_insight(
            "time_budget_overrun", "high",
            f"Recent average is {recent_hours:g} streaming hours per week, "
            f"above the stated {data.weekly_hours_available:g}-hour weekly budget.",
            "Reduce the schedule or revise the available-hours estimate before adding tasks.",
            "Review stream time and workload after two weeks.",
            ["stream_minutes"], cautious=False,
        ))

    if viewers.direction == "down" and viewers.change_percent is not None and viewers.change_percent <= -15:
        insights.append(_insight(
            "viewer_decline", "high",
            f"Stream-minute-weighted average viewers decreased by "
            f"{abs(viewers.change_percent):g}% between the halves.",
            "Compare similar days, categories and stream lengths; test one change at a time.",
            "Track the next two weeks of comparable streams.",
            ["average_viewers", "stream_minutes"],
        ))
    elif viewers.direction == "up" and viewers.change_percent is not None and viewers.change_percent >= 15:
        insights.append(_insight(
            "viewer_growth", "medium",
            f"Stream-minute-weighted average viewers increased by {viewers.change_percent:g}%.",
            "Identify repeatable stream elements before changing the schedule.",
            "Check whether the trend persists over the next two weeks.",
            ["average_viewers"],
        ))

    if data.primary_goal == "discovery" and clips.recent == 0:
        insights.append(_insight(
            "no_clips", "high",
            "No clips were recorded as published in the recent reporting period.",
            "Try one or two original short clips per week from already recorded streams.",
            "Log published clips and available reach for the next two weeks.",
            ["clips_published"],
        ))
    elif data.primary_goal == "discovery" and clips.recent is None:
        notes.append("Discovery recommendation limited: publishing frequency is unknown.")
    if clips.recent is not None and clips.recent > 0 and clip_views.direction == "down":
        insights.append(_insight(
            "clip_reach_decline", "medium",
            "Average weekly reported clip views decreased between the observation halves.",
            "Compare clips with similar topics and publication windows; review openings.",
            "Review the next two weeks of clips with comparable measurement windows.",
            ["clips_published", "clip_views"],
        ))

    if unique.direction == "up" and returning.direction == "down":
        insights.append(_insight(
            "returning_viewers_decline", "medium",
            "Reported unique viewers increased while returning-viewer counts decreased.",
            "Test consistent recurring content and a clear next-stream announcement.",
            "Compare returner counts for similar stream schedules over two weeks.",
            ["unique_viewers", "returning_viewers"],
        ))

    if follows.direction == "down" and unique.direction == "up":
        insights.append(_insight(
            "follows_not_tracking_reach", "medium",
            "Unique viewers increased but new follows declined.",
            "Make the channel value proposition and next-stream schedule clearer.",
            "Compare new follows per unique viewer over subsequent weeks.",
            ["unique_viewers", "follows"],
        ))

    if not insights:
        insights.append(_insight(
            "baseline_review", "low",
            "No large, supported signal was detected with the available weekly aggregates.",
            "Keep the schedule stable and collect consistent metrics before intervening.",
            "Collect two additional weeks, then compare with the same definitions.",
            [c.metric for c in comparisons if c.direction != "unavailable"][:3],
        ))

    # High-priority resource constraints come before growth experiments.
    # Keep discovery order within each priority level; alphabetic ordering
    # would accidentally rank "no_clips" ahead of "time_budget_overrun".
    weights = {"high": 0, "medium": 1, "low": 2}
    insights.sort(key=lambda item: weights[item.priority])
    return CreatorIntelligenceResponse(
        analyzed_weeks=len(weeks), comparisons=comparisons,
        insights=insights, missing_metrics=missing, data_quality_notes=notes,
        limitations=[
            "Offline prototype, not a verified causal diagnosis or growth forecast.",
            "Metrics are manually supplied and are not independently verified.",
            "Comparisons use weekly aggregates; stream-level variation is not available.",
            "Clip views from unequal publication ages are not directly comparable.",
            "No personal account connection, scraping or language-model calls.",
        ],
    )
