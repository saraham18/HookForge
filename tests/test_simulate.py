import json

import pytest

from hookforge.simulate import (
    PERSONAS,
    _parse_json_object,
    simulate,
)
from tests.conftest import FakeAnthropic


def test_parse_json_tolerates_surrounding_prose():
    raw = 'Sure! {"monologue": "meh", "scroll_stop_probability": 30, "biggest_flaw": "vague"} done'
    data = _parse_json_object(raw)
    assert data["scroll_stop_probability"] == 30


def test_parse_json_raises_when_absent():
    with pytest.raises(ValueError):
        _parse_json_object("no json here")


def test_simulate_runs_every_persona_and_scores(config):
    payload = json.dumps(
        {"monologue": "skeptical", "scroll_stop_probability": 80, "biggest_flaw": "hype"}
    )
    fake = FakeAnthropic(payload)
    report = simulate(config, "we built X", platform="x", client=fake)
    assert len(report.reactions) == len(PERSONAS)
    assert report.average_score == 80.0
    assert "STRONG" in report.verdict


def test_score_is_clamped(config):
    payload = json.dumps(
        {"monologue": "x", "scroll_stop_probability": 999, "biggest_flaw": ""}
    )
    report = simulate(config, "draft", client=FakeAnthropic(payload))
    assert all(r.scroll_stop_probability == 100 for r in report.reactions)


def test_verdict_weak_when_low(config):
    payload = json.dumps(
        {"monologue": "boring", "scroll_stop_probability": 10, "biggest_flaw": "fluff"}
    )
    report = simulate(config, "draft", client=FakeAnthropic(payload))
    assert "WEAK" in report.verdict
