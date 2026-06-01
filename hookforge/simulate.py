"""The Zero-Click Hook Simulator.

Stress-test a draft post against three distinct, cynical reader personas before
you publish. Each persona returns an unvarnished internal monologue plus a
scroll-stop probability (0-100). This is the feature standard schedulers lack:
it tells you *why* a fast scroller would keep scrolling past your hook.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .config import Config
from .llm import complete

PERSONAS: dict[str, str] = {
    "tired_developer": (
        "The Tired Developer: highly skeptical, allergic to hype and buzzwords, "
        "smells marketing from a mile away, only respects concrete technical "
        "substance and proof. Has seen a thousand 'revolutionary' tools."
    ),
    "hurried_executive": (
        "The Hurried Executive: wants the bottom-line value in the first three "
        "words, has zero patience, will scroll instantly unless there's a clear "
        "outcome, number, or ROI. Hates fluff and long setups."
    ),
    "genz_marketer": (
        "The Gen-Z Marketer: allergic to corporate speak and cringe, values "
        "authenticity, humor, and a real point of view, instantly bored by "
        "anything that sounds like a press release or a LinkedIn 'thought leader'."
    ),
}

SYSTEM = (
    "You role-play as a specific, cynical social media reader scrolling a fast "
    "feed. You react honestly and bluntly, the way a real person thinks but "
    "never says out loud. You are hard to impress."
)

# We ask for strict JSON so the result is machine-scoreable.
_INSTRUCTIONS = (
    "Here is a draft {platform} post you just scrolled past:\n\n"
    '"""\n{text}\n"""\n\n'
    "React as this persona ONLY:\n{persona}\n\n"
    "Return a JSON object with EXACTLY these keys and nothing else:\n"
    '  "monologue": your blunt 1-2 sentence internal reaction,\n'
    '  "scroll_stop_probability": integer 0-100 (chance you stop scrolling),\n'
    '  "biggest_flaw": the single weakest thing about the hook (short phrase).\n'
    "Output only the JSON object."
)


@dataclass
class PersonaReaction:
    persona: str
    monologue: str
    scroll_stop_probability: int
    biggest_flaw: str


@dataclass
class SimulationReport:
    text: str
    platform: str
    reactions: list[PersonaReaction] = field(default_factory=list)

    @property
    def average_score(self) -> float:
        if not self.reactions:
            return 0.0
        return round(
            sum(r.scroll_stop_probability for r in self.reactions)
            / len(self.reactions),
            1,
        )

    @property
    def verdict(self) -> str:
        avg = self.average_score
        if avg >= 65:
            return "STRONG - likely to stop the scroll"
        if avg >= 45:
            return "OKAY - workable but the hook can be sharper"
        return "WEAK - rewrite the hook before publishing"


def _parse_json_object(raw: str) -> dict:
    """Extract the first JSON object from a model response, tolerantly."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in response: {raw!r}")
    return json.loads(raw[start : end + 1])


def _parse_json_array(raw: str) -> list:
    """Extract the first JSON array from a model response, tolerantly."""
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON array found in response: {raw!r}")
    return json.loads(raw[start : end + 1])


_PERSONA_GEN_SYSTEM = (
    "You build realistic audience personas for testing marketing copy. You make "
    "them specific and true to life, not flattering caricatures - real people are "
    "busy, distracted, and hard to impress."
)

_PERSONA_GEN_INSTRUCTIONS = (
    "Target audience / demographic:\n{audience}\n"
    "{brand_block}\n"
    "Create {count} DISTINCT personas representing real, specific people in this "
    "audience as they scroll a fast social feed. Vary their age, role, mood, and "
    "what makes them stop vs. skip. Keep them honest and a little hard to impress.\n"
    "Return ONLY a JSON array of {count} objects, each with EXACTLY:\n"
    '  "key": a short snake_case identifier,\n'
    '  "description": 1-2 sentences on who they are and exactly what they reward '
    "or punish in a post.\n"
    "Output only the JSON array."
)


def generate_personas(
    config: Config,
    audience: str,
    *,
    count: int = 3,
    brand: str | None = None,
    client: Any | None = None,
) -> dict[str, str]:
    """Generate `count` reader personas tailored to a target demographic.

    The returned mapping plugs straight into ``simulate(..., personas=...)``.
    """
    brand_block = (
        f"\nThe brand they'd be hearing from has this guide:\n{brand.strip()}\n"
        if brand
        else ""
    )
    prompt = _PERSONA_GEN_INSTRUCTIONS.format(
        audience=audience.strip(), brand_block=brand_block, count=count
    )
    raw = complete(
        config,
        _PERSONA_GEN_SYSTEM,
        prompt,
        client=client,
        max_tokens=800,
        temperature=0.9,
    )
    personas: dict[str, str] = {}
    for i, item in enumerate(_parse_json_array(raw)):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or f"persona_{i + 1}").strip().replace(" ", "_")
        if key in personas:
            key = f"{key}_{i + 1}"
        desc = str(item.get("description", "")).strip()
        if desc:
            personas[key] = desc
    if not personas:
        raise ValueError(f"Could not parse any personas from: {raw!r}")
    return personas


def _coerce_reaction(persona_key: str, data: dict) -> PersonaReaction:
    try:
        score = int(data.get("scroll_stop_probability", 0))
    except (TypeError, ValueError):
        score = 0
    return PersonaReaction(
        persona=persona_key,
        monologue=str(data.get("monologue", "")).strip(),
        scroll_stop_probability=max(0, min(100, score)),
        biggest_flaw=str(data.get("biggest_flaw", "")).strip(),
    )


def simulate(
    config: Config,
    text: str,
    *,
    platform: str = "x",
    client: Any | None = None,
    personas: dict[str, str] | None = None,
) -> SimulationReport:
    """Run the draft past every persona and collect their reactions."""
    personas = personas or PERSONAS
    report = SimulationReport(text=text, platform=platform)
    for key, description in personas.items():
        prompt = _INSTRUCTIONS.format(
            platform=platform, text=text, persona=description
        )
        raw = complete(
            config,
            SYSTEM,
            prompt,
            client=client,
            max_tokens=400,
            temperature=0.8,
        )
        report.reactions.append(_coerce_reaction(key, _parse_json_object(raw)))
    return report
