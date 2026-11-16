"""Eigenständiger HTML-Bericht (eine Datei, ohne externe Abhängigkeiten).

Alle Texte aus dem Chat stammen von fremden Personen und werden konsequent maskiert.
"""
from html import escape
from pathlib import Path

from .evaluation import EvaluationReport
from .fusion import CATEGORY_LABELS, format_hms
from .models import HuntResult

COLORS = {"funny": "#f5b301", "hype": "#9146ff", "shock": "#ff4d6d", "fail": "#7a8599",
          "tension": "#20c997", "loud": "#4dabf7", "reaction": "#adb5bd"}

TEXT = {
    "de": {"title": "Clip Hunter – Ergebnis", "mode": "Analyse", "duration": "Länge",
           "chat": "Chat", "candidates": "Kandidaten", "time": "Zeit", "category": "Art",
           "confidence": "Sicherheit", "score": "Wertung", "why": "Warum",
           "samples": "Chat-Auszug", "open": "Im VOD öffnen", "file": "Datei",
           "limits": "Grenzen", "eval": "Abgleich mit Zuschauer-Clips",
           "coverage": "Abdeckung", "weighted": "nach Aufrufen", "precision": "Trefferquote",
           "moments": "Community-Momente", "none": "Keine Kandidaten gefunden.",
           "high": "hoch", "medium": "mittel", "low": "niedrig",
           "level": {"none": "kein Chat", "low": "wenig Chat", "active": "aktiver Chat"},
           "hit": "getroffen von Platz", "miss": "nicht getroffen",
           "ai_yes": "KI: clipwürdig", "ai_no": "KI: eher nicht", "ai_cut": "KI-Schnitt",
           "hook": "Hook", "caption": "Caption", "ai_model": "KI-Modell",
           "ai_reviewed": "geprüft"},
    "en": {"title": "Clip Hunter – result", "mode": "Analysis", "duration": "Length",
           "chat": "Chat", "candidates": "Candidates", "time": "Time", "category": "Type",
           "confidence": "Confidence", "score": "Score", "why": "Why",
           "samples": "Chat excerpt", "open": "Open in VOD", "file": "File",
           "limits": "Limitations", "eval": "Comparison with viewer clips",
           "coverage": "Coverage", "weighted": "by views", "precision": "Precision",
           "moments": "Community moments", "none": "No candidates found.",
           "high": "high", "medium": "medium", "low": "low",
           "level": {"none": "no chat", "low": "small chat", "active": "active chat"},
           "hit": "matched by rank", "miss": "not matched",
           "ai_yes": "AI: clip-worthy", "ai_no": "AI: probably not", "ai_cut": "AI cut",
           "hook": "Hook", "caption": "Caption", "ai_model": "AI model",
           "ai_reviewed": "reviewed"},
}

STYLE = """
body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
background:#0e0e12;color:#e9e9ef}
main{max-width:1000px;margin:0 auto;padding:32px 20px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 12px}
.meta{color:#a1a1b5;margin-bottom:18px}.meta span{margin-right:18px}
.note{background:#1d1d27;border-left:3px solid #f5b301;padding:10px 14px;border-radius:6px;
margin:12px 0;color:#d8d8e2}
svg{width:100%;height:auto;background:#17171f;border-radius:10px}
.card{background:#17171f;border:1px solid #262633;border-radius:12px;padding:16px 18px;
margin:12px 0}
.head{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.rank{font-weight:700;font-size:18px;min-width:34px}
.badge{padding:2px 10px;border-radius:999px;font-size:13px;font-weight:600;color:#0e0e12}
.conf{font-size:13px;color:#a1a1b5}
.bar{height:6px;background:#262633;border-radius:3px;width:120px;overflow:hidden}
.bar i{display:block;height:100%;background:#9146ff}
ul{margin:8px 0 0 18px;padding:0}li{margin:2px 0}
.samples{margin-top:8px;color:#c9c9d6;font-size:14px}
.ai{margin-top:10px;padding:10px 12px;background:#1d1d27;border-radius:8px}
.ai .title{font-weight:700;font-size:16px}.ai .tags{color:#bf94ff;font-size:13px}
.ai .verdict{font-size:13px;font-weight:600}.ai .yes{color:#20c997}.ai .no{color:#a1a1b5}
.samples code{background:#232330;padding:1px 6px;border-radius:4px;margin-right:6px}
a{color:#bf94ff}table{border-collapse:collapse;width:100%}
td,th{text-align:left;padding:6px 8px;border-bottom:1px solid #262633;font-size:14px}
"""


def _timeline(result: HuntResult) -> str:
    duration = result.duration_seconds or max(
        (item.end_seconds for item in result.candidates), default=1)
    duration = max(duration, 1)
    parts = ['<svg viewBox="0 0 1000 70" role="img" aria-label="timeline">',
             '<line x1="10" y1="45" x2="990" y2="45" stroke="#3a3a4a" stroke-width="2"/>']
    hours = int(duration // 3600)
    for hour in range(hours + 1):
        x = min(975.0, max(14.0, 10 + 980 * (hour * 3600) / duration))
        parts.append(f'<text x="{x:.1f}" y="66" fill="#77778a" font-size="11" '
                     f'text-anchor="middle">{hour}h</text>')
    for item in result.candidates:
        x = 10 + 980 * item.anchor_seconds / duration
        radius = 4 + item.score / 20
        color = COLORS.get(item.category, "#adb5bd")
        parts.append(f'<circle cx="{x:.1f}" cy="45" r="{radius:.1f}" fill="{color}">'
                     f'<title>#{item.rank} {format_hms(item.anchor_seconds)}</title></circle>')
        parts.append(f'<text x="{x:.1f}" y="{38 - radius:.1f}" fill="#e9e9ef" font-size="11" '
                     f'text-anchor="middle">{item.rank}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render_report(result: HuntResult, *, evaluation: EvaluationReport | None = None,
                  exported: dict[int, Path] | None = None,
                  report_path: Path | None = None) -> str:
    t = TEXT[result.language]
    labels = CATEGORY_LABELS[result.language]
    rows = []
    for item in result.candidates:
        color = COLORS.get(item.category, "#adb5bd")
        time_range = f"{format_hms(item.start_seconds)}–{format_hms(item.end_seconds)}"
        link = (f' · <a href="{escape(item.vod_link)}" target="_blank" rel="noopener noreferrer">'
                f'{t["open"]}</a>' if item.vod_link else "")
        file_link = ""
        if exported and item.rank in exported:
            target = exported[item.rank]
            href = target.name
            if report_path is not None:
                try:
                    href = target.relative_to(report_path.parent).as_posix()
                except ValueError:
                    href = target.as_uri()
            file_link = f' · {t["file"]}: <a href="{escape(href)}">{escape(target.name)}</a>'
        reasons = "".join(f"<li>{escape(reason)}</li>" for reason in item.reasons)
        samples = ""
        if item.chat and item.chat.sample_messages:
            codes = "".join(f"<code>{escape(text)}</code>" for text in item.chat.sample_messages)
            samples = f'<div class="samples">{t["samples"]}: {codes}</div>'
        ai_html = _ai_html(item, t)
        rows.append(
            f'<div class="card"><div class="head"><span class="rank">#{item.rank}</span>'
            f'<strong>{time_range}</strong>'
            f'<span class="badge" style="background:{color}">{escape(labels[item.category])}'
            f'</span><span class="conf">{t["confidence"]}: {t[item.confidence]}</span>'
            f'<span class="bar" title="{t["score"]} {item.score}"><i style="width:{item.score}%">'
            f'</i></span><span class="conf">{item.score}/100</span>{link}{file_link}</div>'
            f'{ai_html}<ul>{reasons}</ul>{samples}</div>'
        )
    meta = [f'<span>{t["mode"]}: {escape(result.mode)}</span>']
    if result.duration_seconds:
        meta.append(f'<span>{t["duration"]}: {format_hms(result.duration_seconds)}</span>')
    if result.chat:
        meta.append(f'<span>{t["chat"]}: {t["level"][result.chat.level]} '
                    f'({result.chat.median_chatters_per_minute:g}/min)</span>')
    if result.ai_model:
        meta.append(f'<span>{t["ai_model"]}: {escape(result.ai_model)} '
                    f'({result.ai_reviewed} {t["ai_reviewed"]})</span>')
    note = f'<div class="note">{escape(result.alignment_note)}</div>' \
        if result.alignment_note else ""
    eval_html = _evaluation_html(evaluation, t) if evaluation else ""
    limits = "".join(f"<li>{escape(text)}</li>" for text in result.limitations)
    body = "".join(rows) if rows else f"<p>{t['none']}</p>"
    return (
        f'<!DOCTYPE html><html lang="{result.language}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{t["title"]}</title><style>{STYLE}</style></head><body><main>'
        f'<h1>{t["title"]}</h1><div class="meta">{"".join(meta)}</div>{note}'
        f'{_timeline(result)}<h2>{t["candidates"]} ({len(result.candidates)})</h2>{body}'
        f'{eval_html}<h2>{t["limits"]}</h2><ul>{limits}</ul></main></body></html>'
    )


def _ai_html(item, t: dict) -> str:
    review = item.ai
    if review is None:
        return ""
    verdict = (f'<span class="verdict yes">{t["ai_yes"]}</span>' if review.clipworthy
               else f'<span class="verdict no">{t["ai_no"]}</span>')
    parts = [(f'<div class="ai">{verdict} · {round(review.confidence * 100)} % · '
              f'{t["ai_cut"]}: {format_hms(review.start_seconds)}–'
              f'{format_hms(review.end_seconds)}')]
    if review.title:
        parts.append(f'<div class="title">{escape(review.title)}</div>')
    if review.hook:
        parts.append(f'<div>{t["hook"]}: {escape(review.hook)}</div>')
    if review.caption:
        parts.append(f'<div>{t["caption"]}: {escape(review.caption)}</div>')
    if review.hashtags:
        tags = " ".join("#" + escape(tag) for tag in review.hashtags)
        parts.append(f'<div class="tags">{tags}</div>')
    parts.append("</div>")
    return "".join(parts)


def _evaluation_html(report: EvaluationReport, t: dict) -> str:
    def pct(value: float | None) -> str:
        return "–" if value is None else f"{round(value * 100)} %"

    rows = []
    for moment in report.moments:
        status = (f'{t["hit"]} {moment.matched_rank}' if moment.matched_rank
                  else t["miss"])
        titles = escape(" / ".join(moment.titles))
        rows.append(f"<tr><td>{format_hms(moment.start_seconds)}</td><td>{moment.clips}</td>"
                    f"<td>{moment.views}</td><td>{status}</td><td>{titles}</td></tr>")
    return (
        f'<h2>{t["eval"]}</h2><div class="meta"><span>{t["coverage"]}: '
        f'{pct(report.coverage)} ({t["weighted"]}: {pct(report.view_weighted_coverage)})</span>'
        f'<span>{t["precision"]} (Top {report.top_n}): {pct(report.precision_at_n)}</span>'
        f'<span>{t["moments"]}: {report.community_moments}</span></div>'
        f'<div class="note">{escape(report.note)}</div>'
        f'<table><tr><th>{t["time"]}</th><th>Clips</th><th>Views</th><th></th><th></th></tr>'
        f'{"".join(rows)}</table>'
    )
