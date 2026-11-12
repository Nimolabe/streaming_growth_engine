"""Stable contracts shared by future agents and their API clients."""
from enum import Enum

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    CONTENT_STRATEGIST = "content_strategist"
    TREND_SCOUT = "trend_scout"
    CLIP_HUNTER = "clip_hunter"
    GROWTH_ANALYST = "growth_analyst"
    SETUP_ADVISOR = "setup_advisor"


class AgentStatus(str, Enum):
    PLANNED = "planned"
    PROTOTYPE = "prototype"
    READY = "ready"


class AgentInfo(BaseModel):
    name: AgentName
    status: AgentStatus
    description: str


class ContentPlanRequest(BaseModel):
    platform: str = Field(min_length=2, max_length=40)
    category: str = Field(min_length=2, max_length=80)
    audience: str = Field(min_length=2, max_length=120)
    language: str = Field(default="de", pattern=r"^(de|en)$")


class ContentIdea(BaseModel):
    title: str
    explanation: str



class WeeklyPlanRequest(ContentPlanRequest):
    """User-provided inputs only. No scraped or private channel data."""

    weekly_hours: int = Field(ge=2, le=40, description="Total weekly creator time, including preparation")
    stream_days: int = Field(ge=1, le=7)
    primary_goal: str = Field(default="consistency", pattern=r"^(consistency|discovery|community)$")


class WeeklyTask(BaseModel):
    day: int = Field(ge=1, le=7)
    kind: str
    title: str
    minutes: int = Field(gt=0)
    details: str


class WeeklyPlanResponse(BaseModel):
    agent: AgentName = AgentName.CONTENT_STRATEGIST
    prototype: bool = True
    generator: str = "deterministic_rules_v1"
    language: str
    weekly_minutes: int
    allocated_minutes: int
    goal: str
    tasks: list[WeeklyTask]
    note: str
