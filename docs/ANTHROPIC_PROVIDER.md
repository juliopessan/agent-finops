# Anthropic Provider Adapter

`runtime/anthropic_provider.py` implements the `ProviderClient` contract with the official Anthropic Python SDK and Messages API.

## Installation

```bash
pip install -r requirements-pilot.txt
```

## Environment

```bash
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_SMOKE_MODEL="claude-sonnet-4-20250514"
export ANTHROPIC_INPUT_PRICE_PER_MILLION="0"
export ANTHROPIC_OUTPUT_PRICE_PER_MILLION="0"
export ANTHROPIC_CACHE_WRITE_PRICE_PER_MILLION="0"
export ANTHROPIC_CACHE_READ_PRICE_PER_MILLION="0"
```

Pricing remains deployment configuration. The adapter separately accounts for standard input, output, cache creation and cache read usage before returning the measured cost to the Guardian gateway.

## Smoke test

```bash
python scripts/verify_pilot_runtime.py --live-anthropic
```

## Runtime usage

```python
from runtime.anthropic_provider import AnthropicMessagesProvider, AnthropicPricing

provider = AnthropicMessagesProvider(
    pricing=AnthropicPricing(
        input_per_million_usd=3.0,
        output_per_million_usd=15.0,
    )
)
response = provider.complete(
    model="claude-sonnet-4-20250514",
    payload="Return a concise migration assessment.",
    max_output_tokens=500,
    instructions="Use only the supplied context.",
)
```

The adapter concatenates text content blocks, records `input_tokens`, `output_tokens`, `cache_creation_input_tokens` and `cache_read_input_tokens`, and preserves the raw SDK response for diagnostics.
