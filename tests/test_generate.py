import pytest

from hookforge.generate import build_prompt, generate_post, supported_platforms
from tests.conftest import FakeAnthropic


def test_supported_platforms():
    plats = supported_platforms()
    assert "x" in plats and "instagram" in plats


def test_build_prompt_includes_limit_and_brief():
    prompt = build_prompt("an open source tool", "x")
    assert "280" in prompt
    assert "an open source tool" in prompt


def test_build_prompt_rejects_unknown_platform():
    with pytest.raises(ValueError):
        build_prompt("x", "myspace")


def test_generate_post_uses_model_and_returns_text(config):
    fake = FakeAnthropic("stop the scroll: we built it in a weekend")
    post = generate_post(config, "a tool", "x", client=fake)
    assert post.platform == "x"
    assert post.text == "stop the scroll: we built it in a weekend"
    assert post.char_count == len(post.text)
    # The configured model is actually passed through.
    assert fake.last_kwargs["model"] == "test-model"
