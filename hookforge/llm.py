"""Thin wrapper around the Anthropic Messages API.

The SDK import is lazy so the package installs and unit-tests run without the
SDK (or an API key) present. Pass your own ``client`` to inject a fake in tests.
"""
from __future__ import annotations

from typing import Any

from .config import Config


def build_client(config: Config) -> Any:
    config.require(ANTHROPIC_API_KEY=config.anthropic_api_key)
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - exercised only without SDK
        raise RuntimeError(
            "The 'anthropic' package is required for generation. "
            "Install it with: pip install anthropic"
        ) from exc
    return anthropic.Anthropic(api_key=config.anthropic_api_key)


def complete(
    config: Config,
    system: str,
    prompt: str,
    *,
    client: Any | None = None,
    max_tokens: int = 1024,
    temperature: float = 1.0,
) -> str:
    """Return the text of a single-turn completion."""
    client = client or build_client(config)
    message = client.messages.create(
        model=config.model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    # Concatenate any text blocks in the response.
    parts = []
    for block in message.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()
