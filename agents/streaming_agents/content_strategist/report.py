"""Ausgabe des Wochenplans: Text für die Konsole und ein eigenständiger HTML-Bericht.

Alle Texte im HTML werden maskiert; die Spielnamen kommen aus der Eingabe.
"""
from datetime import datetime
from html import escape

from .models import ContentPlan, StreamPlan

TEXT = {
    "de": {"title": "Content-Plan der Woche", "games": "Spiele", "genre": "Genre",
           "stream": "Stream", "prep": "Vorbereitung", "format": "Format", "stream_title": "Titel", "alt": "Andere Titel",
           "tags": "Tags", "run": "Ablauf", "clip": "Clip danach", "hook": "Hook fürs Kurzvideo",
           "measure": "Messgröße", "why": "Warum dieses Format", "when": "Warum diese Uhrzeit",
           "review": "Wochenrückblick", "series": "Mini-Serie", "budget": "Zeitbudget",
           "notes": "Hinweise", "limits": "Twitch-Grenzen", "limitations": "Grenzen dieses Plans",
           "created": "Erstellt", "min": "min", "stream_min": "Streams", "prep_min": "Vorbereitung",
           "clip_min": "Clips", "review_min": "Rückblick", "free_min": "nicht verplant",
           "of": "von", "chat": {"none": "ohne Chat", "low": "kleiner Chat", "active": "aktiver Chat"},
           "check": "Kategorie-Check", "break": "Pausen"},
    "en": {"title": "Weekly content plan", "games": "Games", "genre": "Genre",
           "stream": "Stream", "prep": "Preparation", "format": "Format", "stream_title": "Title", "alt": "Other titles",
           "tags": "Tags", "run": "Run of show", "clip": "Clip afterwards", "hook": "Hook for a short",
           "measure": "Measurement", "why": "Why this format", "when": "Why this time",
           "review": "Weekly review", "series": "Mini-series", "budget": "Time budget",
           "notes": "Notes", "limits": "Twitch limits", "limitations": "Limits of this plan",
           "created": "Created", "min": "min", "stream_min": "Streams", "prep_min": "Preparation",
           "clip_min": "Clips", "review_min": "Review", "free_min": "unplanned",
           "of": "of", "chat": {"none": "no chat", "low": "small chat", "active": "active chat"},
           "check": "Category check", "break": "Breaks"},
}


def _when(item: StreamPlan) -> str:
    return f"{item.stream.label} {item.stream.start}–{item.stream.end}"


def render_text(plan: ContentPlan) -> str:
    t = TEXT[plan.language]
    lines = [t["title"], "=" * len(t["title"])]
    for game in plan.games:
        line = f"{game.name}: {game.genre_label}"
        if game.category_check:
            line += f" · {game.category_check}"
        lines.append(line)
    for item in plan.streams:
        lines += [
            "",
            (f"{item.number}. {_when(item)} ({item.stream.minutes} {t['min']}) · {item.game} · "
             f"{item.format_name} [{t['chat'][item.needs_chat]}]"),
            f"   {t['stream_title']}: {item.title}",
            f"   {t['alt']}: " + " | ".join(item.title_alternatives),
            f"   {t['tags']}: {', '.join(item.tags)}",
            f"   {t['prep']}: {item.preparation.label} {item.preparation.start}–"
            f"{item.preparation.end} – " + "; ".join(item.prep_steps),
        ]
        lines += [f"   {index}. {step}" for index, step in enumerate(item.run_of_show, start=1)]
        if item.break_note:
            lines.append(f"   {item.break_note}")
        lines += [
            f"   {t['clip']} ({item.clip_day}): {item.clip_idea}",
            f"   {t['hook']}: {item.hook}",
            f"   {t['measure']}: {item.measurement}",
            f"   {t['when']}: {item.timing_reason}",
        ]
    lines += ["", f"{t['review']} ({plan.review.day}, {plan.review.minutes} {t['min']}):"]
    lines += [f"   – {question}" for question in plan.review.questions]
    if plan.series:
        lines += ["", f"{t['series']}: {plan.series.format_name} · {plan.series.game}"]
        lines += [f"   – {episode}" for episode in plan.series.episodes]
    b = plan.budget
    lines += ["", (f"{t['budget']}: {b.weekly_minutes} {t['min']} = {t['stream_min']} "
                   f"{b.stream_minutes} + {t['prep_min']} {b.preparation_minutes} + "
                   f"{t['clip_min']} {b.clip_minutes} + {t['review_min']} {b.review_minutes} + "
                   f"{t['free_min']} {b.unplanned_minutes}")]
    lines += ["", f"{t['notes']}:"] + [f"• {note}" for note in plan.notes]
    lines += [f"• {plan.twitch_limits}"]
    return "\n".join(lines)


STYLE = """
body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0e0e12;color:#e9e9ef}
main{max-width:900px;margin:0 auto;padding:32px 16px 60px;overflow-wrap:anywhere}h1{font-size:26px;margin:0 0 6px}
h2{font-size:19px;margin:28px 0 8px}.meta{color:#a1a1b5;margin-bottom:18px}
.card{background:#17171f;border:1px solid #262633;border-radius:12px;padding:16px;margin:14px 0}
.card h3{margin:0 0 4px;font-size:17px}.sub{color:#a1a1b5;font-size:13px}
dl{margin:10px 0 0;display:grid;grid-template-columns:minmax(0,170px) minmax(0,1fr);gap:6px 12px}
dt{color:#a1a1b5;font-size:13px}dd{margin:0;overflow-wrap:anywhere}
.tag{display:inline-block;background:#262633;border-radius:999px;padding:1px 9px;margin:2px 4px 2px 0;font-size:12px}
ol,ul{margin:4px 0 0 18px;padding:0}
@media (max-width:560px){dl{grid-template-columns:minmax(0,1fr)}dt{margin-top:6px}}
"""


def _card(item: StreamPlan, t: dict) -> str:
    tags = "".join(f"<span class=\"tag\">{escape(tag)}</span>" for tag in item.tags)
    run = "".join(f"<li>{escape(step)}</li>" for step in item.run_of_show)
    prep = "".join(f"<li>{escape(step)}</li>" for step in item.prep_steps)
    rows = [
        (t["stream_title"], escape(item.title)),
        (t["alt"], "<br>".join(escape(text) for text in item.title_alternatives)),
        (t["tags"], tags),
        (t["prep"], (f"{escape(item.preparation.label)} {item.preparation.start}–"
                     f"{item.preparation.end}<ul>{prep}</ul>")),
        (t["run"], f"<ol>{run}</ol>"),
    ]
    if item.break_note:
        rows.append((t["break"], escape(item.break_note)))
    rows += [
        (t["clip"], f"{escape(item.clip_day)}: {escape(item.clip_idea)}"),
        (t["hook"], escape(item.hook)),
        (t["measure"], escape(item.measurement)),
        (t["why"], escape(item.why)),
        (t["when"], escape(item.timing_reason)),
    ]
    body = "".join(f"<dt>{escape(label)}</dt><dd>{value}</dd>" for label, value in rows)
    return (
        f"<section class=\"card\"><h3>{item.number}. {escape(_when(item))} · {escape(item.game)}</h3>"
        f"<div class=\"sub\">{escape(item.format_name)} · {escape(item.genre_label)} · "
        f"{item.stream.minutes} {escape(t['min'])} · {escape(t['chat'][item.needs_chat])}</div>"
        f"<dl>{body}</dl></section>"
    )


def render_html(plan: ContentPlan, created: datetime | None = None) -> str:
    t = TEXT[plan.language]
    created = created or datetime.now().astimezone()
    stamp = created.strftime("%d.%m.%Y %H:%M" if plan.language == "de" else "%Y-%m-%d %H:%M")
    games = "".join(
        f"<li><strong>{escape(game.name)}</strong> – {escape(game.genre_label)}"
        + (f"<br><span class=\"sub\">{escape(t['check'])}: {escape(game.category_check)}</span>"
           if game.category_check else "") + "</li>"
        for game in plan.games)
    cards = "".join(_card(item, t) for item in plan.streams)
    review = "".join(f"<li>{escape(question)}</li>" for question in plan.review.questions)
    series = ""
    if plan.series:
        episodes = "".join(f"<li>{escape(episode)}</li>" for episode in plan.series.episodes)
        series = (f"<h2>{escape(t['series'])}</h2><p>{escape(plan.series.format_name)} · "
                  f"{escape(plan.series.game)}</p><ol>{episodes}</ol>")
    b = plan.budget
    budget = (f"{b.weekly_minutes} {t['min']}: {t['stream_min']} {b.stream_minutes}, "
              f"{t['prep_min']} {b.preparation_minutes}, {t['clip_min']} {b.clip_minutes}, "
              f"{t['review_min']} {b.review_minutes}, {t['free_min']} {b.unplanned_minutes}")
    notes = "".join(f"<li>{escape(note)}</li>" for note in plan.notes)
    limitations = "".join(f"<li>{escape(text)}</li>" for text in plan.limitations)
    return (
        f"<!DOCTYPE html><html lang=\"{plan.language}\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{escape(t['title'])}</title><style>{STYLE}</style></head><body><main>"
        f"<h1>{escape(t['title'])}</h1><div class=\"meta\">{escape(t['created'])}: {escape(stamp)}"
        f" · {escape(plan.version)}</div>"
        f"<h2>{escape(t['games'])}</h2><ul>{games}</ul>{cards}"
        f"<h2>{escape(t['review'])} ({escape(plan.review.day)}, {plan.review.minutes} "
        f"{escape(t['min'])})</h2><ul>{review}</ul>{series}"
        f"<h2>{escape(t['budget'])}</h2><p>{escape(budget)}</p>"
        f"<h2>{escape(t['notes'])}</h2><ul>{notes}<li>{escape(plan.twitch_limits)}</li></ul>"
        f"<h2>{escape(t['limitations'])}</h2><ul>{limitations}</ul></main></body></html>"
    )
