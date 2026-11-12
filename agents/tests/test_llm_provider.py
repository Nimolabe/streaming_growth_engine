"""Offline checks for the opt-in LLM provider: NO API calls or charges."""
from types import SimpleNamespace

import pytest

from streaming_agents.contracts import ContentPlanRequest
from streaming_agents.llm.openai_provider import OpenAIConfig, OpenAIResponsesProvider
from streaming_agents.llm.provider import ProviderError
from streaming_agents.llm.service import generate_ai_content_plan


def request():
    return ContentPlanRequest(
        platform="Twitch", category="Minecraft", audience="German beginners", language="de"
    )


class MockResponses:
    def __init__(self, payload, status="completed"):
        self.payload = payload
        self.status = status
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            status=self.status,
            output=[
                SimpleNamespace(
                    type="message",
                    content=[SimpleNamespace(type="output_text", text=self.payload)],
                )
            ],
            usage=SimpleNamespace(input_tokens=110, output_tokens=130),
        )


def provider(payload, **config_kwargs):
    responses = MockResponses(payload)
    config = OpenAIConfig(model="example-model", **config_kwargs)
    return OpenAIResponsesProvider(config, SimpleNamespace(responses=responses)), responses


GOOD = """{
    "ideas": [
        {"title": "Minecraft challenge", "explanation": "Invite the audience to select a challenge."},
        {"title": "Minecraft basics", "explanation": "Teach one accessible building skill."},
        {"title": "Minecraft recap", "explanation": "Make a highlight of your own recording."}
    ]
}"""


def test_valid_output_with_mock_no_network():
    adapter, transport = provider(GOOD)
    result = generate_ai_content_plan(request(), adapter)
    assert len(result.ideas) == 3
    assert result.input_tokens == 110
    assert result.output_tokens == 130
    assert result.prototype is True
    assert transport.calls[0]["store"] is False
    assert transport.calls[0]["text"]["format"]["strict"] is True
    assert transport.calls[0]["max_output_tokens"] <= 1200


@pytest.mark.parametrize(
    "payload",
    [
        "{bad-json",
        '{"ideas": []}',
        '{"ideas": [{"title": "ok", "explanation": "too short"}]}',
        ('{"ideas": [{"title": "Valid title", "explanation": "Long enough to pass"}, '
        '{"title": "Valid title", "explanation": "Long enough to pass"}, '
        '{"title": "Valid title", "explanation": "Long enough to pass"}], "secret": 1}'),
    ],
)
def test_invalid_model_output_is_rejected(payload):
    adapter, _ = provider(payload)
    with pytest.raises(ProviderError, match="invalid structured response"):
        adapter.generate(request())


def test_cost_preflight_blocks_request_before_network():
    adapter, transport = provider(GOOD, estimated_max_usd=0.00001)
    with pytest.raises(ProviderError, match="Estimated cost cap"):
        adapter.generate(request())
    assert transport.calls == []


def test_incomplete_response_is_rejected():
    adapter, transport = provider(GOOD)
    transport.status = "incomplete"
    with pytest.raises(ProviderError, match="not completed"):
        adapter.generate(request())


def test_provider_exception_does_not_leak_sensitive_text():
    class BrokenResponses:
        def create(self, **kwargs):
            raise RuntimeError("sk-secret-placeholder: external error details")

    adapter = OpenAIResponsesProvider(
        OpenAIConfig(model="example-model"),
        SimpleNamespace(responses=BrokenResponses()),
    )
    with pytest.raises(ProviderError) as error:
        adapter.generate(request())
    assert "sk-secret-placeholder" not in str(error.value)


def test_missing_key_blocks_provider_creation(monkeypatch):
    from streaming_agents.llm.openai_provider import create_openai_provider

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="not configured"):
        create_openai_provider(OpenAIConfig(model="example-model"))


def test_invalid_provider_configuration_is_blocked():
    with pytest.raises(ProviderError, match="explicit model"):
        OpenAIResponsesProvider(
            OpenAIConfig(model=""), SimpleNamespace(responses=MockResponses(GOOD))
        )
