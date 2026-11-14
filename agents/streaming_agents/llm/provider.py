"""Model-provider contract, bounded requests, and validated responses.

No network calls occur until generate() is explicitly invoked.
"""
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from streaming_agents.contracts import ContentPlanRequest


class GeneratedIdea(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=140)
    explanation: str = Field(min_length=10, max_length=600)


class GeneratedContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ideas: list[GeneratedIdea] = Field(min_length=3, max_length=3)


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ModelResult:
    content: GeneratedContent
    model: str
    usage: Usage


class ModelProvider(Protocol):
    def generate(self, request: ContentPlanRequest) -> ModelResult: ...


class ProviderError(Exception):
    """A sanitized, user-facing error. Do not include raw API messages or keys."""


def validate_request_size(request: ContentPlanRequest) -> None:
    # Limit input exposure, unpredictable costs and pathological payloads.
    if len(request.model_dump_json().encode("utf-8")) > 1400:
        raise ProviderError("Content planning inputs are too large.")
