"""Local developer-only entrypoint. No public paid endpoint is exposed."""
import argparse
import json
import os

from streaming_agents.contracts import ContentPlanRequest

from .openai_provider import OpenAIConfig, create_openai_provider
from .provider import ProviderError
from .service import generate_ai_content_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in local AI Content Strategist test")
    parser.add_argument("--live", action="store_true", help="I understand this may incur API charges")
    parser.add_argument("--platform", default="Twitch")
    parser.add_argument("--category", default="Minecraft")
    parser.add_argument("--audience", default="Beginner streamers")
    parser.add_argument("--language", choices=["de", "en"], default="de")
    args = parser.parse_args()

    if not args.live:
        print("No request sent. Add --live to explicitly permit a paid API call.")
        return 0

    try:
        request = ContentPlanRequest(
            platform=args.platform,
            category=args.category,
            audience=args.audience,
            language=args.language,
        )
        config = OpenAIConfig(
            model=os.environ.get("SGE_LLM_MODEL", ""),
            estimated_max_usd=float(os.environ.get("SGE_ESTIMATED_MAX_USD", "0.02")),
            input_usd_per_million=float(os.environ.get("SGE_INPUT_USD_PER_M", "1.0")),
            output_usd_per_million=float(os.environ.get("SGE_OUTPUT_USD_PER_M", "5.0")),
        )
        provider = create_openai_provider(config)
        result = generate_ai_content_plan(request, provider)
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        return 0
    except (ProviderError, ValueError) as exc:
        print(f"Unable to generate content plan: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
