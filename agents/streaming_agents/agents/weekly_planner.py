"""A transparent, offline weekly content planner. No model calls or external data."""
from ..contracts import WeeklyPlanRequest, WeeklyPlanResponse, WeeklyTask


def make_weekly_plan(request: WeeklyPlanRequest) -> WeeklyPlanResponse:
    """Distribute a bounded time budget across streams and preparation.

    Always returns an honest template plan, not performance predictions.
    """
    total = request.weekly_hours * 60
    # Split 70% live streams, 30% content preparation, review and community.
    stream_minutes = (total * 7 // 10) // request.stream_days
    if stream_minutes < 30:
        raise ValueError("Not enough hours for the selected number of stream days")
    allocated_stream = stream_minutes * request.stream_days
    support = total - allocated_stream
    en = request.language == "en"
    category = request.category.strip()
    platform = request.platform.strip()
    audience = request.audience.strip()

    focuses = {
        "consistency": (
            "Eine feste Stream-Routine für regelmäßige Zuschauer",
            "Create a repeatable streaming routine",
        ),
        "discovery": (
            "Neue Zuschauer durch kurze Highlights erreichen",
            "Reach new viewers with short highlights",
        ),
        "community": (
            "Aktive Zuschauerfragen und Community-Interaktion",
            "Build audience interaction and community participation",
        ),
    }
    focus_de, focus_en = focuses[request.primary_goal]
    focus = focus_en if en else focus_de

    tasks = [
        WeeklyTask(
            day=day,
            kind="stream",
            title=(f"{category} live on {platform}" if en else f"{category} live auf {platform}"),
            minutes=stream_minutes,
            details=(
                f"Focus: {focus}. Include an interactive segment for {audience}."
                if en else f"Schwerpunkt: {focus}. Plane einen interaktiven Teil für {audience}."
            ),
        )
        for day in range(1, request.stream_days + 1)
    ]

    # Short-form editing, topic preparation and a weekly review are always planned.
    sections = (
        [
            ("preparation", "Prepare topics and stream titles", "Prepare 2-3 titles and a clear opening."),
            ("clip", "Create a short highlight", "Use only your own recordings or licensed material."),
            ("review", "Reflect on your week", "Note what worked and adapt next week's plan."),
        ]
        if en else [
            ("preparation", "Themen und Stream-Titel vorbereiten", "Bereite 2–3 Titel und einen klaren Einstieg vor."),
            ("clip", "Einen kurzen Highlight-Clip erstellen", "Nutze nur eigene Aufnahmen oder erlaubtes Material."),
            ("review", "Die Woche auswerten", "Notiere, was gut lief, und passe die nächste Woche an."),
        ]
    )
    weights = [45, 35, 20]
    minutes = [support * w // 100 for w in weights]
    minutes[-1] = support - sum(minutes[:-1])
    for index, ((kind, title, details), duration) in enumerate(zip(sections, minutes)):
        if duration > 0:
            tasks.append(
                WeeklyTask(
                    day=min(7, request.stream_days + index + 1),
                    kind=kind,
                    title=title,
                    minutes=duration,
                    details=details,
                )
            )

    return WeeklyPlanResponse(
        language=request.language,
        weekly_minutes=total,
        allocated_minutes=sum(t.minutes for t in tasks),
        goal=request.primary_goal,
        tasks=tasks,
        note=(
            "Offline prototype. Times are suggestions, not growth guarantees. Take breaks."
            if en else
            "Offline-Prototyp. Zeiten sind Vorschläge, keine Wachstumsgarantie. Plane Pausen ein."
        ),
    )
