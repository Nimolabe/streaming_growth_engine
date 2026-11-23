"""Lokale Entwicklungs-API der KI-Agenten.

Noch nicht öffentlich: keine Anmeldung, keine Rate-Limits. Nur auf 127.0.0.1 betreiben.
Alle Endpunkte liegen unter /api/v1 und sind nach Agent gruppiert.
"""
from fastapi import APIRouter, FastAPI, HTTPException

from .agents.creator_intelligence import analyze_creator
from .agents.creator_intelligence_contracts import (
    CreatorIntelligenceRequest,
    CreatorIntelligenceResponse,
)
from .agents.creator_strategy import build_creator_strategy
from .agents.creator_strategy_contracts import StrategyDecisionV2, StrategyRequestV2
from .agents.creator_strategy_review import (
    ExperimentReviewRequestV2,
    ExperimentReviewV2,
    review_creator_experiment,
)
from .agents.v3_contracts import ContentStrategyV3, CreatorProfileV3
from .agents.v3_recommender import generate_strategy_v3
from .agents.weekly_planner import make_weekly_plan
from .category_check.analysis import analyze, local_time_from_offset, parse_window
from .category_check.models import CategoryCheckRequest, CategoryCheckResult
from .clip_hunter.hunter import hunt
from .clip_hunter.models import ChatHuntRequest, HuntResult
from .contracts import AgentInfo, WeeklyPlanRequest, WeeklyPlanResponse
from .registry import AGENTS

API_PREFIX = "/api/v1"

app = FastAPI(
    title="Streaming Growth Engine – KI-Agenten",
    version="0.2.0",
    description="Lokale Entwicklungs-API. Noch nicht produktionsreif: keine Anmeldung.",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
)
api = APIRouter(prefix=API_PREFIX)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/agents", response_model=list[AgentInfo], tags=["Allgemein"])
def list_agents() -> list[AgentInfo]:
    return AGENTS


# ---------- Content Strategist ----------
@api.post("/content/strategy", response_model=ContentStrategyV3, tags=["Content Strategist"])
def content_strategy(profile: CreatorProfileV3) -> ContentStrategyV3:
    """Erklärbare Format-Empfehlungen und Mini-Serien (offline, regelbasiert)."""
    try:
        return generate_strategy_v3(profile)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@api.post("/content/category-check", response_model=CategoryCheckResult,
          tags=["Content Strategist"])
def content_category_check(request: CategoryCheckRequest) -> CategoryCheckResult:
    """Wertet Twitch-Messungen aus: Platz im Verzeichnis, Publikum und beste Zeiten.

    Die Messungen entstehen lokal mit `python -m streaming_agents.category_check`;
    die API selbst fragt Twitch nicht an.
    """
    try:
        window = parse_window(request.window) if request.window else None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return analyze(request.snapshots, own_viewers=request.own_viewers, language=request.language,
                   to_local=local_time_from_offset(request.utc_offset_minutes), window=window)


@api.post("/content/weekly-plan", response_model=WeeklyPlanResponse, tags=["Content Strategist"])
def weekly_plan(request: WeeklyPlanRequest) -> WeeklyPlanResponse:
    """Verteilt das Wochenbudget auf Streams, Vorbereitung und Nacharbeit."""
    try:
        return make_weekly_plan(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ---------- Growth Analyst ----------
@api.post("/growth/analysis", response_model=CreatorIntelligenceResponse, tags=["Growth Analyst"])
def growth_analysis(data: CreatorIntelligenceRequest) -> CreatorIntelligenceResponse:
    """Vergleicht selbst eingegebene Wochenwerte; keine Kausalaussagen."""
    return analyze_creator(data)


@api.post("/growth/strategy", response_model=StrategyDecisionV2, tags=["Growth Analyst"])
def growth_strategy(request: StrategyRequestV2) -> StrategyDecisionV2:
    """Wählt ein Experiment, das ins verfügbare Zeitbudget passt."""
    return build_creator_strategy(request)


@api.post("/growth/review", response_model=ExperimentReviewV2, tags=["Growth Analyst"])
def growth_review(request: ExperimentReviewRequestV2) -> ExperimentReviewV2:
    """Beschreibt das Ergebnis eines Experiments; nie ein Erfolgsversprechen."""
    return review_creator_experiment(request)


# ---------- Clip Hunter ----------
@api.post("/clips/chat-moments", response_model=HuntResult, tags=["Clip Hunter"])
def clip_chat_moments(request: ChatHuntRequest) -> HuntResult:
    """Findet Clip-Momente nur aus einem Chat-Mitschnitt (Reaktionen, Emotes, Ausschläge)."""
    return hunt(chat_log=request.chat_log, vod_start=request.vod_start,
                settings=request.settings, twitch_video_id=request.twitch_video_id)


app.include_router(api)
