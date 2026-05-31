import types

import pytest

from hookforge.config import Config, MissingCredential
from hookforge.publishers.x import publish_to_x
from hookforge.publishers.instagram import publish_to_instagram


class FakeXClient:
    def __init__(self):
        self.text = None

    def create_tweet(self, text):
        self.text = text
        return types.SimpleNamespace(data={"id": "1234567890"})


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeIGSession:
    """Returns a container id on the first POST, a media id on the second."""

    def __init__(self):
        self.calls = []
        self._responses = [
            FakeResponse({"id": "container_1"}),
            FakeResponse({"id": "media_99"}),
        ]

    def post(self, url, data=None):
        self.calls.append((url, data))
        return self._responses[len(self.calls) - 1]


@pytest.fixture
def x_config():
    return Config(
        env={
            "X_API_KEY": "k",
            "X_API_SECRET": "s",
            "X_ACCESS_TOKEN": "t",
            "X_ACCESS_TOKEN_SECRET": "ts",
        }
    )


@pytest.fixture
def ig_config():
    return Config(env={"IG_ACCESS_TOKEN": "tok", "IG_USER_ID": "42"})


def test_x_publish_returns_url(x_config):
    client = FakeXClient()
    result = publish_to_x(x_config, "hello world", client=client)
    assert client.text == "hello world"
    assert result["id"] == "1234567890"
    assert "1234567890" in result["url"]


def test_x_rejects_overlong_text(x_config):
    with pytest.raises(ValueError):
        publish_to_x(x_config, "a" * 281, client=FakeXClient())


def test_x_requires_credentials():
    with pytest.raises(MissingCredential):
        publish_to_x(Config(env={}), "hi", client=FakeXClient())


def test_instagram_two_step_flow(ig_config):
    session = FakeIGSession()
    result = publish_to_instagram(
        ig_config, "caption", "https://example.com/card.png", session=session
    )
    # Two API calls: create container, then publish.
    assert len(session.calls) == 2
    assert session.calls[0][0].endswith("/42/media")
    assert session.calls[1][1]["creation_id"] == "container_1"
    assert result["id"] == "media_99"


def test_instagram_rejects_non_http_image(ig_config):
    with pytest.raises(ValueError):
        publish_to_instagram(ig_config, "cap", "card.png", session=FakeIGSession())


def test_instagram_requires_credentials():
    with pytest.raises(MissingCredential):
        publish_to_instagram(
            Config(env={}), "cap", "https://x.com/a.png", session=FakeIGSession()
        )
