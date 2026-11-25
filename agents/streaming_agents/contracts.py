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
