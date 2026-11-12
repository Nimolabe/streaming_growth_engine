"""Agent registry. Planned agents are not exposed as working AI products."""

from .contracts import AgentInfo, AgentName, AgentStatus

AGENTS = [
    AgentInfo(
        name=AgentName.CONTENT_STRATEGIST,
        status=AgentStatus.PROTOTYPE,
        description=(
            "Offline curated format recommendations, mini-series and weekly plans; "
            "optional LLM provider remains off by default."
        ),
    ),
    AgentInfo(
        name=AgentName.TREND_SCOUT,
        status=AgentStatus.PLANNED,
        description="Detect growing streaming categories; to reuse the Trend Radar scouts.",
    ),
    AgentInfo(
        name=AgentName.CLIP_HUNTER,
        status=AgentStatus.PROTOTYPE,
        description="Offline audio and scene-change review timestamps from user-owned recordings.",
    ),
    AgentInfo(
        name=AgentName.GROWTH_ANALYST,
        status=AgentStatus.PROTOTYPE,
        description="Offline creator-supplied weekly metrics, conservative comparisons and experiments.",
    ),
    AgentInfo(
        name=AgentName.SETUP_ADVISOR,
        status=AgentStatus.PLANNED,
        description=(
            "Budget-based equipment recommendations; covered by the Setup Intelligence Agent "
            "(backend/setup_agent) instead of a second implementation."
        ),
    ),
]
