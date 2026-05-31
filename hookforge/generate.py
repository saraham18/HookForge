"""Generate platform-native social posts from a product/topic brief."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Config
from .llm import complete

# Per-platform constraints and voice guidance. Keep these declarative so the
# prompt stays auditable and easy to extend with new platforms.
PLATFORMS: dict[str, dict] = {
    "x": {
        "name": "X (Twitter)",
        "limit": 280,
        "guidance": (
            "A single post under 280 characters. Lead with a scroll-stopping "
            "hook in the first line. No external links in the body (they get "
            "throttled). At most 1-2 hashtags. Plain, punchy, lowercase-friendly."
        ),
    },
    "instagram": {
        "name": "Instagram",
        "limit": 2200,
        "guidance": (
            "A caption with a strong first line (the only part shown before "
            "'more'), 2-4 short line-broken value points, one clear CTA, and a "
            "block of 5-10 relevant hashtags at the end. Warm, human, concrete."
        ),
    },
    "linkedin": {
        "name": "LinkedIn",
        "limit": 3000,
        "guidance": (
            "A hook line, a short story or insight in 3-5 line-broken "
            "sentences, and a question CTA. Professional but not corporate. "
            "No more than 3 hashtags."
        ),
    },
}

SYSTEM = (
    "You are a senior growth marketer who writes native, scroll-stopping social "
    "copy. You never sound like generic AI corporate fluff. You write with "
    "specificity, personality, and a clear point of view. Return ONLY the post "
    "text, with no preamble, quotes, or explanation."
)


@dataclass
class Post:
    platform: str
    text: str

    @property
    def char_count(self) -> int:
        return len(self.text)


def supported_platforms() -> list[str]:
    return list(PLATFORMS)


def build_prompt(product: str, platform: str, *, tone: str | None = None) -> str:
    if platform not in PLATFORMS:
        raise ValueError(
            f"Unknown platform '{platform}'. Supported: {', '.join(PLATFORMS)}"
        )
    spec = PLATFORMS[platform]
    tone_line = f"\nDesired tone: {tone}." if tone else ""
    return (
        f"Write a {spec['name']} post promoting the following.\n\n"
        f"BRIEF:\n{product.strip()}\n{tone_line}\n\n"
        f"FORMAT REQUIREMENTS:\n{spec['guidance']}\n"
        f"Hard character limit: {spec['limit']}."
    )


def generate_post(
    config: Config,
    product: str,
    platform: str,
    *,
    tone: str | None = None,
    client: Any | None = None,
) -> Post:
    prompt = build_prompt(product, platform, tone=tone)
    text = complete(
        config,
        SYSTEM,
        prompt,
        client=client,
        max_tokens=1024,
        temperature=1.0,
    )
    return Post(platform=platform, text=text)
