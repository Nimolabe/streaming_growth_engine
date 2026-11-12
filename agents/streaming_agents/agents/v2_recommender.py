"""Deterministic evidence-aware ranking for established content mechanics.

No LLM, external calls, scraping, secret access, predictions or tracking.
All scores are transparent editorial heuristics, not empirical success rates.
"""

from .v2_catalog import FORMATS, SOURCES, Format
from .v2_contracts import ContentStrategyV2, CreatorProfileV2, RecommendationV2

_GROUPS = {
    "tactical": (
        "valorant", "counter-strike", "cs2", "csgo", "rainbow six", "r6", "overwatch"
    ),
    "sandbox": ("minecraft", "terraria", "stardew", "sims", "factorio", "satisfactory"),
    "battle_royale": ("fortnite", "apex", "warzone", "pubg", "battle royale"),
}


def classify_game(category: str) -> str:
    value = category.casefold()
    for group, terms in _GROUPS.items():
        if any(term in value for term in terms):
            return group
    return "general"


def _fit(item: Format, profile: CreatorProfileV2, group: str) -> tuple[int, list[str]]:
    reasons = []
    score = 32
    if item.genre == group and group != "general":
        score += 26
        reasons.append("Passendes Spielgenre" if profile.language == "de" else "Matching game genre")
    elif item.genre == "general":
        score += 12
        reasons.append("Genreübergreifend nutzbar" if profile.language == "de" else "Works across genres")
    else:
        score -= 18
    if item.style == profile.content_style:
        score += 16
        reasons.append("Passt zum Content-Stil" if profile.language == "de" else "Matches content style")
    if item.goal == profile.primary_goal:
        score += 16
        reasons.append("Unterstützt dein Ziel" if profile.language == "de" else "Matches your goal")
    elif item.goal == "consistency":
        score += 4
    if item.min_hours <= profile.weekly_hours:
        score += 8
        reasons.append("Ins Zeitbudget passend" if profile.language == "de" else "Fits time budget")
    else:
        score -= 35
    if profile.channel_size == "new" and item.mechanism in {
        "collaboration", "feedback", "participation", "prediction"
    }:
        score -= 12  # these formats require collaborators or an active chat
    if profile.experience == "beginner" and item.mechanism in {"analysis", "tutorial"}:
        score -= 5  # avoid positioning beginner as an expert
    return max(0, min(100, score)), reasons


def _serialize(
    item: Format, score: int, reasons: list[str], profile: CreatorProfileV2,
) -> RecommendationV2:
    en = profile.language == "en"
    steps = item.steps_en if en else item.steps_de
    concept = item.title_en if en else item.title_de
    category = profile.category
    context = (
        f"Für {profile.audience} auf {profile.platform}: "
        if not en else f"For {profile.audience} on {profile.platform}: "
    )
    caveat = (
        "Bei einem neuen Kanal nicht von einem aktiven Chat ausgehen; "
        "gegebenenfalls mit freiwilligen Mitspielern starten."
        if not en else
        "For a new channel, do not assume active chat; consider willing collaborators."
    )
    return RecommendationV2(
        format_id=item.id,
        title=f"{concept} · {category}",
        rationale=(
            context + ("; ".join(reasons) if reasons else
                       ("Experimentell passende Option" if not en else "Experimental fit"))
        ),
        fit_score=score,
        score_interpretation=(
            "Redaktioneller Eignungswert aus Profil und Regeln, KEINE Erfolgswahrscheinlichkeit."
            if not en else
            "Editorial rules-based profile fit, NOT a chance of success."
        ),
        estimated_min_hours_per_week=item.min_hours,
        stream_run_of_show=list(steps),
        short_video_hook=(item.hook_en if en else item.hook_de),
        short_video_edit=(item.clip_en if en else item.clip_de),
        measurement=(item.metric_en if en else item.metric_de),
        evidence_links=[SOURCES[key] for key in item.source_ids],
        limitations=(
            (caveat + " " if profile.channel_size == "new" and item.mechanism in {
                "collaboration", "feedback", "participation", "prediction"
            } else "") + (
            "Formatidee als Anwendung etablierter Prinzipien; dieser konkrete Ablauf "
            "ist nicht empirisch als erfolgreich nachgewiesen. Quellen belegen "
            "allgemeine Prinzipien, nicht diesen Einzelfall."
            if not en else
            "Format hypothesis based on established principles. No empirical proof "
            "that this exact format will succeed; sources support general principles only."
            )
        ),
    )


def generate_strategy(profile: CreatorProfileV2) -> ContentStrategyV2:
    group = classify_game(profile.category)
    excluded = set(profile.exclude_format_ids)
    options = [
        (score, item, reasons)
        for item in FORMATS
        if item.id not in excluded
        if item.min_hours <= profile.weekly_hours
        if (
            (group == "general" and item.genre == "general")
            or (group != "general" and item.genre in {group, "general"})
        )
        for score, reasons in [_fit(item, profile, group)]
    ]
    options.sort(key=lambda x: (-x[0], x[1].id))
    # Diversify mechanisms before repeating an approach.
    picked: list[tuple[int, Format, list[str]]] = []
    used: set[str] = set()
    for candidate in options:
        if candidate[1].mechanism not in used:
            picked.append(candidate)
            used.add(candidate[1].mechanism)
            if len(picked) == profile.count:
                break
    if len(picked) < profile.count:
        chosen = {item.id for _, item, _ in picked}
        picked.extend(
            candidate for candidate in options
            if candidate[1].id not in chosen
        )
    picked = picked[:profile.count]
    if not picked:
        # Defensive programming: at least one 2-hour general format always remains
        # unless all applicable format IDs are excluded.
        raise ValueError("No matching formats. Remove some exclude_format_ids.")
    en = profile.language == "en"
    return ContentStrategyV2(
        game_group=group,
        total_formats_considered=len(options),
        recommendations=[_serialize(item, score, reasons, profile) for score, item, reasons in picked],
        next_step=(
            "Run one format for two or three sessions, note audience feedback and "
            "compare similar streams before changing multiple variables."
            if en else
            "Teste ein Format zwei bis drei Streams lang. Notiere Rückmeldungen und "
            "vergleiche ähnliche Streams, bevor du mehrere Dinge gleichzeitig änderst."
        ),
        disclaimer=(
            "Offline curated recommendations. No live trends, growth guarantees, "
            "personal channel analytics or AI model calls."
            if en else
            "Offline kuratierte Empfehlungen. Keine Live-Trends, Wachstumsgarantien, "
            "Kanalstatistiken oder Sprachmodellaufrufe."
        ),
    )
