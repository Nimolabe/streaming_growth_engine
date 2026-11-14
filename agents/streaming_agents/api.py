"""Lokale Entwicklungs-API der KI-Agenten.

Noch nicht öffentlich: keine Anmeldung, keine Rate-Limits. Nur auf 127.0.0.1 betreiben.
Alle Endpunkte liegen unter /api/v1 und sind nach Agent gruppiert.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import APIRouter, FastAPI, File, HTTPException, Query, UploadFile

from .agents.clip_evaluation import (
    ClipEvaluationReport,
    ClipEvaluationRequest,
    evaluate_human_labels,
)
from .agents.clip_intelligence import SUPPORTED_SUFFIXES, ClipScanError
from .agents.clip_intelligence_v2 import scan_recording_v2
from .agents.clip_intelligence_v2_contracts import ClipReviewResultV2, ClipScanSettingsV2
from .agents.clip_review_queue_v3 import (
    ClipReviewQueueRequestV3,
    ClipReviewQueueV3,
    make_review_queue,
)
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
from .clip_hunter.hunter import hunt
from .clip_hunter.models import ChatHuntRequest, HuntResult
from .contracts import AgentInfo, WeeklyPlanRequest, WeeklyPlanResponse
from .registry import AGENTS

API_PREFIX = "/api/v1"
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_UPLOAD_SECONDS = 900

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
@api.post("/clips/scan", response_model=ClipReviewResultV2, tags=["Clip Hunter"])
def clip_scan(
    file: Annotated[UploadFile, File()],
    max_candidates: Annotated[int, Query(ge=1, le=10)] = 5,
) -> ClipReviewResultV2:
    """Sucht Audio-Spitzen und Bildwechsel in einer eigenen, kurzen Aufnahme."""
    suffix = Path(file.filename or "").suffix.casefold()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=422, detail="Upload a WAV, MP4, MOV, MKV or WEBM recording."
        )
    settings = ClipScanSettingsV2(
        max_candidates=max_candidates, max_duration_seconds=MAX_UPLOAD_SECONDS
    )
    with TemporaryDirectory(prefix="clip-scan-") as directory:
        recording = Path(directory) / f"recording{suffix}"
        total = 0
        with recording.open("wb") as destination:
            while data := file.file.read(1024 * 1024):
                total += len(data)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413, detail="Recording must be at most 100 MB."
                    )
                destination.write(data)
        try:
            return scan_recording_v2(recording, settings)
        except ClipScanError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


@api.post("/clips/chat-moments", response_model=HuntResult, tags=["Clip Hunter"])
def clip_chat_moments(request: ChatHuntRequest) -> HuntResult:
    """Findet Clip-Momente nur aus einem Chat-Mitschnitt (Reaktionen, Emotes, Ausschläge)."""
    return hunt(chat_log=request.chat_log, vod_start=request.vod_start,
                settings=request.settings, twitch_video_id=request.twitch_video_id)


@api.post("/clips/evaluate", response_model=ClipEvaluationReport, tags=["Clip Hunter"])
def clip_evaluate(request: ClipEvaluationRequest) -> ClipEvaluationReport:
    """Misst vorgeschlagene Zeitpunkte gegen menschliche Markierungen."""
    return evaluate_human_labels(request)


@api.post("/clips/review-queue", response_model=ClipReviewQueueV3, tags=["Clip Hunter"])
def clip_review_queue(request: ClipReviewQueueRequestV3) -> ClipReviewQueueV3:
    """Erzeugt eine verblindete Prüfliste aus vorhandenen Scan-Ergebnissen."""
    return make_review_queue(request)


app.include_router(api)
