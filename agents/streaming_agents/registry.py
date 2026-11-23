"""Agent registry. Planned agents are not exposed as working AI products."""

from .contracts import AgentInfo, AgentName, AgentStatus

AGENTS = [
    AgentInfo(
        name=AgentName.CONTENT_STRATEGIST,
        status=AgentStatus.PROTOTYPE,
        description=(
            "Rule-based weekly plan for small streamers: real days and times within the "
            "streamer's windows, genre-specific formats (9 genres), Twitch-conform titles and "
            "tags, preparation and a clip per stream; times follow category check measurements "
            "on real Twitch directory data when provided. No language model, no costs."
        ),
    ),
    AgentInfo(
        name=AgentName.TREND_SCOUT,
        status=AgentStatus.PLANNED,
        description=(
            "Detect growing streaming categories; planned to build on the category check "
            "measurements (category_check)."
        ),
    ),
    AgentInfo(
        name=AgentName.CLIP_HUNTER,
        status=AgentStatus.PROTOTYPE,
        description=(
            "Offline clip moments from chat reactions (live chat recording, emote types, "
            "alert filtering) and sudden audio spikes; vertical export and viewer-clip check."
        ),
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
            "Budget-based equipment recommendations; the website's setup finder (setups.html) "
            "covers this today. A separate Setup Intelligence Agent is parked in pull request #5."
        ),
    ),
]
