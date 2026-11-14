"""Application-level boundary converting model output to stable contracts."""
from pydantic import BaseModel, Field

from streaming_agents.contracts import ContentIdea, ContentPlanRequest

from .provider import ModelProvider


class AIContentPlanResponse(BaseModel):
    ideas: list[ContentIdea] = Field(min_length=3, max_length=3)
    model: str
    prototype: bool = True
    input_tokens: int
    output_tokens: int
    note: str = "AI-generated suggestions; not verified trend or growth predictions."


def generate_ai_content_plan(
    request: ContentPlanRequest, provider: ModelProvider
) -> AIContentPlanResponse:
    result = provider.generate(request)
    return AIContentPlanResponse(
        ideas=[
            ContentIdea(title=idea.title, explanation=idea.explanation)
            for idea in result.content.ideas
        ],
        model=result.model,
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
    )
