"""Shared test fakes — no network, no API keys, no SDKs required."""
import types

import pytest

from hookforge.config import Config


class FakeBlock:
    def __init__(self, text):
        self.text = text


class FakeMessage:
    def __init__(self, text):
        self.content = [FakeBlock(text)]


class FakeAnthropic:
    """Returns a scripted response; records the last call for assertions."""

    def __init__(self, response_text):
        self._response_text = response_text
        self.last_kwargs = None
        self.messages = types.SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeMessage(self._response_text)


@pytest.fixture
def config():
    # A config with a dummy LLM key so require() passes; we inject fake clients.
    return Config(env={"ANTHROPIC_API_KEY": "test-key", "HOOKFORGE_MODEL": "test-model"})
