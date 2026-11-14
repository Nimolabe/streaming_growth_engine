"""Misst Clip-Kandidaten an den Clips, die Zuschauer selbst erstellt haben.

Viele Zuschauer clippen denselben Moment. Deshalb werden überlappende Zuschauer-Clips zu
einem „Community-Moment“ zusammengefasst. Gemessen wird dann:

- Abdeckung: Anteil der Community-Momente, die ein Kandidat trifft (auch nach Aufrufen
  gewichtet, weil viel gesehene Clips wichtiger sind).
- Trefferquote: Anteil der besten N Kandidaten, die einen Community-Moment treffen.

Zuschauer-Clips sind ein guter, aber unvollständiger Maßstab: Gute Momente, die niemand
geclippt hat, zählen hier als „Fehlalarm“.
"""
from pydantic import BaseModel, Field

from .models import ClipCandidate
from .twitch_api import ViewerClip


class CommunityMoment(BaseModel):
    start_seconds: float
    end_seconds: float
    clips: int = Field(ge=1)
    views: int = Field(ge=0)
    titles: list[str] = Field(default_factory=list, max_length=3)
    matched_rank: int | None = None


class EvaluationReport(BaseModel):
    top_n: int
    community_moments: int
    viewer_clips: int
    covered_moments: int
    coverage: float | None = Field(description="Anteil getroffener Community-Momente")
    view_weighted_coverage: float | None
    precision_at_n: float | None = Field(description="Anteil der Top-N-Kandidaten mit Treffer")
    moments: list[CommunityMoment]
    note: str


def community_moments(clips: list[ViewerClip], merge_gap: float = 5.0) -> list[CommunityMoment]:
    moments: list[CommunityMoment] = []
    for clip in sorted(clips, key=lambda item: item.vod_offset):
        start, end = clip.vod_offset, clip.vod_offset + clip.duration
        if moments and start <= moments[-1].end_seconds + merge_gap:
            last = moments[-1]
            last.end_seconds = max(last.end_seconds, end)
            last.clips += 1
            last.views += clip.view_count
            if clip.title and len(last.titles) < 3 and clip.title not in last.titles:
                last.titles.append(clip.title)
        else:
            moments.append(CommunityMoment(start_seconds=start, end_seconds=end, clips=1,
                                           views=clip.view_count,
                                           titles=[clip.title] if clip.title else []))
    return moments


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def evaluate_against_viewer_clips(candidates: list[ClipCandidate], clips: list[ViewerClip],
                                  top_n: int = 10, min_overlap: float = 3.0,
                                  language: str = "de") -> EvaluationReport:
    moments = community_moments(clips)
    ranked = sorted(candidates, key=lambda item: item.rank)[:top_n]
    hits = 0
    for candidate in ranked:
        matched = False
        for moment in moments:
            if _overlap(candidate.start_seconds, candidate.end_seconds,
                        moment.start_seconds, moment.end_seconds) >= min_overlap:
                matched = True
                if moment.matched_rank is None or candidate.rank < moment.matched_rank:
                    moment.matched_rank = candidate.rank
        hits += matched
    covered = [moment for moment in moments if moment.matched_rank is not None]
    total_views = sum(moment.views for moment in moments)
    de = language == "de"
    if not moments:
        note = ("Keine Zuschauer-Clips mit VOD-Position gefunden – keine Messung möglich."
                if de else "No viewer clips with a VOD position found – nothing to measure.")
    else:
        note = ("Zuschauer-Clips decken nicht alle guten Momente ab; niedrige Trefferquote "
                "heißt nicht automatisch schlechte Kandidaten." if de else
                "Viewer clips do not cover every good moment; a low precision does not "
                "automatically mean poor candidates.")
    return EvaluationReport(
        top_n=top_n,
        community_moments=len(moments),
        viewer_clips=len(clips),
        covered_moments=len(covered),
        coverage=round(len(covered) / len(moments), 3) if moments else None,
        view_weighted_coverage=(round(sum(m.views for m in covered) / total_views, 3)
                                if total_views else None),
        precision_at_n=round(hits / len(ranked), 3) if ranked and moments else None,
        moments=moments,
        note=note,
    )
