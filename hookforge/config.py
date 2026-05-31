"""Configuration loaded from environment variables / a local .env file.

HookForge is bring-your-own-keys: nothing is hard-coded and no key ever leaves
your machine except in the API calls you explicitly trigger.
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MODEL = "claude-sonnet-4-6"


def load_dotenv(path: str | os.PathLike = ".env") -> dict:
    """Minimal .env loader (no third-party dependency).

    Lines of the form KEY=VALUE are read into os.environ without overwriting
    values already set in the real environment. Returns the parsed mapping.
    """
    parsed: dict[str, str] = {}
    p = Path(path)
    if not p.exists():
        return parsed
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        parsed[key] = value
        os.environ.setdefault(key, value)
    return parsed


class MissingCredential(RuntimeError):
    """Raised when an operation needs a credential that isn't configured."""


class Config:
    """Resolved credentials and settings."""

    def __init__(self, env: dict | None = None):
        env = env if env is not None else os.environ
        # LLM
        self.anthropic_api_key = env.get("ANTHROPIC_API_KEY")
        self.model = env.get("HOOKFORGE_MODEL", DEFAULT_MODEL)
        # X / Twitter (OAuth 1.0a user context)
        self.x_api_key = env.get("X_API_KEY")
        self.x_api_secret = env.get("X_API_SECRET")
        self.x_access_token = env.get("X_ACCESS_TOKEN")
        self.x_access_secret = env.get("X_ACCESS_TOKEN_SECRET")
        # Instagram (Meta Graph API)
        self.ig_access_token = env.get("IG_ACCESS_TOKEN")
        self.ig_user_id = env.get("IG_USER_ID")

    def require(self, **named: str | None) -> None:
        """Raise MissingCredential listing every required value that is unset."""
        missing = [name for name, value in named.items() if not value]
        if missing:
            raise MissingCredential(
                "Missing required credential(s): "
                + ", ".join(missing)
                + ". Add them to your environment or .env file "
                "(see .env.example)."
            )

    @classmethod
    def load(cls, dotenv_path: str | os.PathLike = ".env") -> "Config":
        load_dotenv(dotenv_path)
        return cls()
