from __future__ import annotations

import argparse
import json
import os
import sys

from runtime.compressors import HeadroomCompressor
from runtime.openai_provider import OpenAIPricing, OpenAIResponsesProvider


def verify_headroom() -> dict[str, object]:
    sample = "\n".join(
        [
            "INFO workflow completed successfully id=123 duration=10ms",
            "INFO workflow completed successfully id=124 duration=11ms",
            "INFO workflow completed successfully id=125 duration=12ms",
            "ERROR workflow failed id=126 reason=timeout",
        ]
        * 40
    )
    compressed = HeadroomCompressor(model=os.getenv("ZWCA_HEADROOM_MODEL", "gpt-4o-mini")).compress(
        sample, target_tokens=max(len(sample) // 16, 64)
    )
    if not compressed or len(compressed) >= len(sample):
        raise RuntimeError("Headroom smoke test did not reduce the sample payload")
    return {
        "status": "passed",
        "input_chars": len(sample),
        "output_chars": len(compressed),
        "reduction_pct": round((1 - len(compressed) / len(sample)) * 100, 2),
    }


def verify_openai_live(model: str) -> dict[str, object]:
    pricing = OpenAIPricing(
        input_per_million_usd=float(os.getenv("OPENAI_INPUT_PRICE_PER_MILLION", "0")),
        output_per_million_usd=float(os.getenv("OPENAI_OUTPUT_PRICE_PER_MILLION", "0")),
    )
    provider = OpenAIResponsesProvider(pricing=pricing)
    response = provider.complete(
        model=model,
        payload="Reply with exactly: ZWCA provider smoke test passed",
        max_output_tokens=20,
    )
    return {
        "status": "passed",
        "model": model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "measured_cost_usd": response.cost_usd,
        "content": response.content,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-openai", action="store_true")
    parser.add_argument("--model", default=os.getenv("OPENAI_SMOKE_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()

    result: dict[str, object] = {"headroom": verify_headroom()}
    if args.live_openai:
        result["openai"] = verify_openai_live(args.model)
    else:
        result["openai"] = {"status": "skipped", "reason": "use --live-openai"}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
