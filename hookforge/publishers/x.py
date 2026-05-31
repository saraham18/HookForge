"""Publish a post to X (Twitter) using the v2 API via Tweepy.

Requires OAuth 1.0a user-context credentials (a free/basic developer account
with Read+Write). Tweepy is imported lazily.
"""
from __future__ import annotations

from typing import Any

from ..config import Config


def _require_credentials(config: Config) -> None:
    config.require(
        X_API_KEY=config.x_api_key,
        X_API_SECRET=config.x_api_secret,
        X_ACCESS_TOKEN=config.x_access_token,
        X_ACCESS_TOKEN_SECRET=config.x_access_secret,
    )


def _client(config: Config) -> Any:
    _require_credentials(config)
    try:
        import tweepy
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'tweepy' package is required to publish to X. "
            "Install it with: pip install tweepy"
        ) from exc
    return tweepy.Client(
        consumer_key=config.x_api_key,
        consumer_secret=config.x_api_secret,
        access_token=config.x_access_token,
        access_token_secret=config.x_access_secret,
    )


def publish_to_x(config: Config, text: str, *, client: Any | None = None) -> dict:
    """Post a tweet. Returns {'id', 'url'}.

    Pass ``client`` to inject a fake in tests.
    """
    # Validate credentials up front so behaviour is the same whether or not a
    # client is injected (mirrors the Instagram publisher).
    _require_credentials(config)
    if len(text) > 280:
        raise ValueError(
            f"Post is {len(text)} characters; X allows 280. Shorten it first."
        )
    client = client or _client(config)
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return {"id": tweet_id, "url": f"https://x.com/i/web/status/{tweet_id}"}
