"""Eigenständiger HTML-Bericht zum Kategorie-Check (eine Datei, alle Texte maskiert)."""
from datetime import datetime
from html import escape

from .aliases import alias_label
from .models import CategoryCheckResult, CategorySummary

COLORS = {"good": "#20c997", "ok": "#f5b301", "hard": "#ff6b81", "low_demand": "#8b8f99"}
TEXT = {
    "de": {"title": "Kategorie-Check", "own": "Deine Zuschauer", "measured": "Messungen",
           "category": "Kategorie", "channels": "Live-Kanäle", "viewers": "Zuschauer gesamt",
           "median": "Zuschauer pro Kanal (Median)", "top3": "Anteil Top 3", "rank": "Dein Platz",
           "verdict": "Einschätzung", "slots": "Beste Zeiten", "none": "–", "notes": "Hinweise",
           "labels": {"good": "gute Chance", "ok": "machbar", "hard": "schwer", "low_demand": "wenig Publikum"},
           "created": "Erstellt", "lang": "Sprache"},
    "en": {"title": "Category check", "own": "Your viewers", "measured": "Measurements",
           "category": "Category", "channels": "Live channels", "viewers": "Total viewers",
           "median": "Viewers per channel (median)", "top3": "Top 3 share", "rank": "Your position",
           "verdict": "Verdict", "slots": "Best times", "none": "–", "notes": "Notes",
           "labels": {"good": "good chance", "ok": "doable", "hard": "hard", "low_demand": "small audience"},
           "created": "Created", "lang": "Language"},
}
STYLE = """
body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0e0e12;color:#e9e9ef}
main{max-width:1100px;margin:0 auto;padding:32px 20px 60px}h1{font-size:26px;margin:0 0 6px}
.meta{color:#a1a1b5;margin-bottom:22px}.meta span{margin-right:18px}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:820px}
th,td{text-align:left;padding:10px 10px;border-bottom:1px solid #262633;vertical-align:top;font-size:14px}
th{color:#a1a1b5;font-weight:600;font-size:13px}td.num{font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700;color:#0e0e12}
.why{color:#c9c9d6;font-size:13px;margin-top:4px}ul{margin:8px 0 0 18px;padding:0;color:#c9c9d6}
.slots{font-size:13px;color:#c9c9d6}.slot{white-space:nowrap}
.alias{color:#a1a1b5;font-size:13px}
"""


def _num(value: float, lower_bound: bool = False, language: str = "de") -> str:
    if isinstance(value, int):
        text = f"{value:,}".replace(",", ".") if language == "de" else f"{value:,}"
    else:
        text = f"{value:g}".replace(".", ",") if language == "de" else f"{value:g}"
    return f"{text}+" if lower_bound else text


def _row(item: CategorySummary, t: dict, language: str) -> str:
    rank = (f"&gt; {item.median_rank - 1}" if item.rank_is_lower_bound
            else str(item.median_rank))
    slots = "<br>".join(f"<span class=\"slot\">{escape(slot.label)}</span>"
                        for slot in item.best_slots) or t["none"]
    lang = "" if item.language == "any" else f" ({escape(item.language)})"
    aliases = "".join(f"<div class=\"alias\">{escape(alias_label(alias, item.category))}</div>"
                      for alias in item.aliases)
    return (
        f"<tr><td><strong>{escape(item.category)}</strong>{lang}{aliases}"
        f"<div class=\"why\">{item.measurements} {escape(t['measured'])}</div></td>"
        f"<td class=\"num\">{_num(item.median_channels, item.channels_is_lower_bound, language)}</td>"
        f"<td class=\"num\">{_num(item.median_total_viewers, item.channels_is_lower_bound, language)}</td>"
        f"<td class=\"num\">{_num(item.median_viewers_per_channel, False, language)}</td>"
        f"<td class=\"num\">{round(item.top3_share * 100)} %</td>"
        f"<td class=\"num\">{rank}</td>"
        f"<td><span class=\"badge\" style=\"background:{COLORS[item.verdict]}\">"
        f"{escape(t['labels'][item.verdict])}</span><div class=\"why\">{escape(item.verdict_text)}</div></td>"
        f"<td class=\"slots\">{slots}</td></tr>"
    )


def render_report(result: CategoryCheckResult, created: datetime | None = None) -> str:
    t = TEXT[result.language]
    created = created or datetime.now().astimezone()
    rows = "".join(_row(item, t, result.language) for item in result.categories)
    notes = "".join(f"<li>{escape(text)}</li>" for text in result.notes)
    head = "".join(f"<th>{escape(t[key])}</th>" for key in
                   ("category", "channels", "viewers", "median", "top3", "rank", "verdict", "slots"))
    return (
        f"<!DOCTYPE html><html lang=\"{result.language}\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{escape(t['title'])}</title><style>{STYLE}</style></head><body><main>"
        f"<h1>{escape(t['title'])}</h1><div class=\"meta\">"
        f"<span>{escape(t['own'])}: {result.own_viewers}</span>"
        f"<span>{escape(t['measured'])}: {result.measurements}</span>"
        f"<span>{escape(t['created'])}: {escape(created.strftime('%d.%m.%Y %H:%M' if result.language == 'de' else '%Y-%m-%d %H:%M'))}</span></div>"
        f"<div class=\"wrap\"><table><tr>{head}</tr>{rows}</table></div>"
        f"<h2>{escape(t['notes'])}</h2><ul>{notes}</ul></main></body></html>"
    )
