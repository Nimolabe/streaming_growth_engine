"""Content Strategist V3: explainable recommendations and viable mini-series.

Fully offline. No network, models, tracking, or channel access.
"""

from .v2_catalog import FORMATS, SOURCES, Format
from .v2_recommender import classify_game
from .v3_contracts import (
    ContentStrategyV3,
    CreatorProfileV3,
    FormatRecommendationV3,
    SeriesEpisodeV3,
    WorkloadV3,
)
from .v3_game_knowledge import SITUATIONS, game_key

CHAT_DEPENDENT = frozenset({
    "coach-my-round",
    "clip-feedback",
    "round-prediction",
    "build-from-comments",
    "community-rule-world",
    "format-pilot",
    "audience-choice",
    "viewer-questions",
})
COLLAB_DEPENDENT = frozenset({"guest-explainer"})
GENRE_GAME_MAP = {"valorant": "tactical", "minecraft": "sandbox", "fortnite": "battle_royale"}


def _stage(profile: CreatorProfileV3) -> str:
    if profile.average_viewers < 5:
        return "early"
    if profile.average_viewers < 50:
        return "growing"
    return "established"


def _chat_capacity(profile: CreatorProfileV3) -> str:
    if profile.active_chatters < 3 or profile.average_viewers < 3:
        return "low"
    if profile.active_chatters < 15:
        return "moderate"
    return "active"


def _workload(profile: CreatorProfileV3) -> WorkloadV3:
    total = 60 * profile.hours_per_week
    live = 65 * total // 100
    # Every planned stream needs enough time to be meaningful; reject unrealistic plans.
    if live // profile.streams_per_week < 30:
        raise ValueError(
            "Too many streams for available hours; reduce streams_per_week or add time."
        )
    prep = 15 * total // 100
    edit = 15 * total // 100
    review = total - live - prep - edit
    return WorkloadV3(
        total_minutes=total,
        livestream_minutes=live,
        preparation_minutes=prep,
        editing_minutes=edit,
        review_minutes=review,
    )


def _eligible(item: Format, profile: CreatorProfileV3, group: str) -> bool:
    if item.genre not in {group, "general"}:
        return False
    if item.min_hours > profile.hours_per_week:
        return False
    if item.id in profile.exclude_format_ids:
        return False
    # Protect zero/small chat creators from non-viable interaction-heavy formats.
    if _chat_capacity(profile) == "low" and item.id in CHAT_DEPENDENT:
        return False
    return not (profile.average_viewers < 5 and item.id in COLLAB_DEPENDENT)


def _score(item: Format, profile: CreatorProfileV3, group: str) -> tuple[int, list[str]]:
    en = profile.language == "en"
    why: list[str] = []
    result = 10
    if item.genre == group and group != "general":
        result += 28
        why.append("Spielgenre passt" if not en else "Game genre fits")
    else:
        result += 10
        why.append("Flexibel einsetzbar" if not en else "Flexible across genres")
    if item.style == profile.style:
        result += 15
        why.append("Passender Content-Stil" if not en else "Matches creator style")
    if item.goal == profile.goal:
        result += 15
        why.append("Passt zum Wachstumsziel" if not en else "Matches creator goal")
    if item.min_hours <= profile.hours_per_week:
        result += 8
        why.append("Im Zeitbudget machbar" if not en else "Fits time budget")
    if item.id not in CHAT_DEPENDENT and item.id not in COLLAB_DEPENDENT:
        result += 8
        if _chat_capacity(profile) == "low":
            why.append("Ohne aktiven Chat möglich" if not en else "Works without live chat")
    elif _chat_capacity(profile) != "low":
        result += 3
    if profile.experience == "beginner" and item.mechanism in {"analysis", "tutorial"}:
        result -= 6
        why.append("Fachliche Vorbereitung nötig" if not en else "Requires preparation")
    elif profile.experience == "beginner" and item.mechanism in {"progress", "experiment"}:
        result += 5
        why.append("Lernfortschritt statt Expertenrolle" if not en else "Learning journey, not expert claims")
    elif profile.experience == "advanced" and item.mechanism in {"analysis", "comparison"}:
        result += 5
        why.append("Erfahrung für tiefere Analyse" if not en else "Experience supports deeper analysis")
    if profile.goal == "discovery" and item.mechanism in {
        "analysis", "transformation", "comparison", "experiment", "progress"
    }:
        result += 5

    audience = profile.audience.casefold()
    novice = any(word in audience for word in (
        "anfänger", "einsteiger", "beginner", "new players", "neulinge"
    ))
    expert = any(word in audience for word in (
        "ranked", "competitive", "kompetitiv", "high elo", "fortgeschritten"
    ))
    humor = any(word in audience for word in (
        "humor", "comedy", "lustig", "funny"
    ))
    if novice and item.mechanism == "tutorial":
        result += 7
        why.append("Einsteigerorientierte Erklärung" if not en else "Beginner-friendly format")
    elif expert and item.mechanism in {"analysis", "comparison"}:
        result += 5
        why.append("Passend zu kompetitiver Zielgruppe" if not en else "Competitive audience fit")
    elif humor and item.mechanism == "recap":
        result += 5
        why.append("Unterhaltsames Format" if not en else "Humor-oriented format")

    if profile.platform == "youtube" and item.mechanism == "tutorial":
        result += 4
        why.append("Gut als erklärendes Video" if not en else "Suits explanatory video")
    elif profile.platform == "tiktok" and item.mechanism in {
        "recap", "transformation", "comparison"
    }:
        result += 4
        why.append("Gut als Kurzvideo-Konzept" if not en else "Suits short-form video")
    return min(100, max(0, result)), why


# Specific, observable checks replace the same generic metric for every solo format.
SOLO_METRICS: dict[str, tuple[str, str]] = {
    "decision-review": (
        "Ist die Entscheidung aus Ausgangslage und Auflösung verständlich? Notiere Zuschauerbindung bis zur Auflösung, falls Messdaten vorhanden sind.",
        "Can viewers follow the decision and reveal? Record retention to the payoff if analytics are available.",
    ),
    "role-swap": (
        "Vergleiche pro Folge eine konkrete Positionierungsentscheidung vor und nach dem Rollenwechsel.",
        "Compare one positioning decision before and after the role change per episode.",
    ),
    "micro-skill": (
        "Dokumentiere, ob derselbe Crosshair-Fehler in zwei vergleichbaren Spielsituationen erneut vorkommt.",
        "Check whether the same crosshair error occurs in two comparable situations.",
    ),
    "skill-diary": (
        "Vergleiche den ersten und letzten Versuch mit denselben Kriterien, ohne Fortschritt zu versprechen.",
        "Compare the first and last attempt using the same criteria without promising improvement.",
    ),
    "two-approaches": (
        "Prüfe, ob beide Methoden am selben Ziel und anhand derselben Kriterien verglichen werden.",
        "Check whether both approaches use the same goal and comparison criteria.",
    ),
}


def _render(
    item: Format, score: int, explanations: list[str],
    profile: CreatorProfileV3, key: str | None,
) -> FormatRecommendationV3:
    en = profile.language == "en"
    scenario = SITUATIONS.get(key or "", {}).get(item.id)
    title = (item.title_en if en else item.title_de) + " · " + profile.game
    steps = list(item.steps_en if en else item.steps_de)
    hook = item.hook_en if en else item.hook_de
    if scenario is not None:
        title = scenario.title_en if en else scenario.title_de
        # Replace the generic setup with a precise game scenario.
        steps[0] = scenario.setup_en if en else scenario.setup_de
        hook = scenario.hook_en if en else scenario.hook_de
    adapted_for_solo = False
    if _chat_capacity(profile) == "low" and item.id == "decision-review":
        steps[1] = (
            "Pause your own footage before the outcome, explain both choices, "
            "then reveal and evaluate. No chat vote is needed."
            if en else
            "Stoppe die eigene Aufnahme vor dem Ausgang, erkläre beide Optionen "
            "und löse dann auf. Funktioniert auch ohne aktiven Live-Chat."
        )
        adapted_for_solo = True

    sources = [SOURCES[source_id] for source_id in item.source_ids]
    if key == "valorant" and scenario is not None:
        sources.append("https://playvalorant.com/en-us/agents/")
    note = (
        "Sources describe general content/analytics principles and, where applicable, "
        "game roles. They do not validate outcomes for this exact format."
        if en else
        "Quellen erklären allgemeine Content-/Analyseprinzipien und ggf. Spielrollen; "
        "sie belegen keinen Erfolg dieses konkreten Formats."
    )
    metric = item.metric_en if en else item.metric_de
    if _chat_capacity(profile) == "low":
        solo_metric = SOLO_METRICS.get(item.id)
        if solo_metric is not None:
            metric = solo_metric[1] if en else solo_metric[0]
        elif any(term in metric.casefold() for term in (
            "chat", "zuschauer", "vote", "viewer", "feedback"
        )):
            metric = (
                "Review the quality of one completed example; do not depend on chat."
                if en else
                "Prüfe die Qualität eines umgesetzten Beispiels ohne Chat-Abhängigkeit."
            )

    clip_structure = item.clip_en if en else item.clip_de
    if _chat_capacity(profile) == "low" and item.id == "decision-review":
        clip_structure = (
            "Show the key decision, freeze just before the outcome, explain "
            "the two options, then reveal what happened."
            if en else
            "Kritische Entscheidung zeigen, vor dem Ausgang kurz stoppen, "
            "zwei Optionen erklären und anschließend die Auflösung zeigen."
        )
    return FormatRecommendationV3(
        format_id=item.id,
        title=title,
        reason=(
            (f"Für {profile.audience} auf {profile.platform}: " if not en else
             f"For {profile.audience} on {profile.platform}: ")
            + "; ".join(explanations)
        ),
        fit_score=score,
        score_method=(
            "Transparent editorial rule score, not a likelihood of growth."
            if en else
            "Transparenter redaktioneller Regelwert, keine Wachstumswahrscheinlichkeit."
        ),
        requires_live_chat=item.id in CHAT_DEPENDENT,
        adapted_for_solo=adapted_for_solo,
        estimated_hours_per_week=item.min_hours,
        stream_steps=steps,
        short_video_hook=hook,
        short_video_structure=clip_structure,
        measurement=metric,
        minimum_viable_test=(
            "Test once with your own recording, review the result and change one element."
            if en else
            "Einmal mit eigener Aufnahme testen, Ergebnis prüfen und nur ein Element ändern."
        ),
        evidence_links=list(dict.fromkeys(sources)),
        evidence_note=note,
    )


def _series(
    first: FormatRecommendationV3, profile: CreatorProfileV3,
) -> list[SeriesEpisodeV3]:
    en = profile.language == "en"
    titles = (
        ("Baseline", "Verbesserung", "Vergleich")
        if not en else ("Baseline", "Iteration", "Comparison")
    )
    focuses = (
        (
            "Zeige eine echte Ausgangsszene. Erkläre das Problem, bevor du es auflöst.",
            "Ändere genau eine Methode und dokumentiere eine neue Szene.",
            "Vergleiche beide Szenen fair und benenne auch Grenzen und Rückschläge.",
        )
        if not en else (
            "Show one real baseline clip. Explain the problem before the payoff.",
            "Change one approach and record another comparable clip.",
            "Compare fairly, including limitations and setbacks.",
        )
    )
    outputs = (
        (
            "Eine dokumentierte Ausgangssituation mit klaren Vergleichskriterien",
            "Eine neue Aufnahme, in der genau eine Entscheidung verändert wurde",
            "Ein Vergleichsvideo mit Ergebnis, Grenzen und einer nächsten Hypothese",
        ) if not en else (
            "A documented baseline with clear comparison criteria",
            "A follow-up clip with one deliberately changed decision",
            "A comparison video with a result, limitations and the next hypothesis",
        )
    )
    checks = (
        (
            "Ist die Ausgangssituation verständlich und nachvollziehbar?",
            "Ist nur ein wesentlicher Faktor geändert und dokumentiert?",
            first.measurement,
        ) if not en else (
            "Is the baseline understandable and reproducible?",
            "Was only one meaningful variable changed and recorded?",
            first.measurement,
        )
    )
    result: list[SeriesEpisodeV3] = []
    for i in range(3):
        # Each episode has its own purpose and a concrete deliverable.
        focus = f"{focuses[i]} {first.stream_steps[i]}"
        result.append(
            SeriesEpisodeV3(
                episode=i + 1,
                title=f"{titles[i]}: {first.title}",
                focus=focus,
                expected_output=outputs[i],
                check_after=checks[i],
            )
        )
    return result


def generate_strategy_v3(profile: CreatorProfileV3) -> ContentStrategyV3:
    workload = _workload(profile)
    key = game_key(profile.game)
    group = GENRE_GAME_MAP.get(key, classify_game(profile.game))
    choices = []
    for item in FORMATS:
        if _eligible(item, profile, group):
            score, explanations = _score(item, profile, group)
            choices.append((score, item, explanations))
    choices.sort(key=lambda x: (-x[0], x[1].id))

    # Strong differentiation: use each underlying content mechanic once
    # before adding another similar entry, then preserve stable score order.
    selected: list[tuple[int, Format, list[str]]] = []
    used: set[str] = set()
    for candidate in choices:
        if candidate[1].mechanism not in used:
            selected.append(candidate)
            used.add(candidate[1].mechanism)
            if len(selected) >= profile.ideas_requested:
                break
    if len(selected) < profile.ideas_requested:
        selected_ids = {c[1].id for c in selected}
        for candidate in choices:
            if candidate[1].id not in selected_ids:
                selected.append(candidate)
                if len(selected) >= profile.ideas_requested:
                    break
    selected = selected[: profile.ideas_requested]
    if not selected:
        raise ValueError(
            "No viable formats for the chosen inputs. Try more hours or fewer exclusions."
        )

    recommendations = [
        _render(item, score, reasons, profile, key)
        for score, item, reasons in selected
    ]
    early = _stage(profile)
    en = profile.language == "en"
    return ContentStrategyV3(
        game_group=group,
        creator_stage=early,
        chat_capacity=_chat_capacity(profile),
        recommendations=recommendations,
        series_plan=_series(recommendations[0], profile),
        workload=workload,
        evaluation_guide=(
            [
                "Try the same format in three comparable episodes and keep a consistent schedule.",
                "Use your own stream summaries: compare retention, repeat viewing and feedback.",
                "Change one production choice at a time; do not treat small samples as proof.",
            ] if en else [
                "Teste das Format in drei vergleichbaren Folgen bei möglichst festen Zeiten.",
                "Vergleiche eigene Stream-Zusammenfassungen, Rückkehrer und Feedback.",
                "Ändere jeweils nur eine Sache; kleine Stichproben sind kein Erfolgsbeweis.",
            ]
        ),
        limitations=(
            [
                "Offline editorial prototype: no live trends, model calls or predictive analytics.",
                "Platform and game details may change; check current game versions.",
                "Method sources do not prove any individual concept will succeed.",
            ] if en else [
                "Redaktioneller Offline-Prototyp: keine Live-Trends, Sprachmodelle oder Prognosen.",
                "Plattform und Spielmechaniken können sich ändern.",
                "Die Quellen beweisen nicht die Wirksamkeit einzelner Formate.",
            ]
        ),
    )
