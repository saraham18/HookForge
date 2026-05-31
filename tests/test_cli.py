import hookforge.cli as cli
from hookforge.config import Config
from hookforge.generate import Post
from hookforge.simulate import PersonaReaction, SimulationReport


def test_run_command_generates_and_simulates(monkeypatch, capsys):
    monkeypatch.setattr(
        cli, "generate_post", lambda *a, **k: Post(platform=a[2], text="hook line")
    )

    def fake_sim(config, text, platform="x", **kw):
        return SimulationReport(
            text=text,
            platform=platform,
            reactions=[
                PersonaReaction("tired_developer", "meh", 70, "hype"),
            ],
        )

    monkeypatch.setattr(cli, "simulate", fake_sim)

    parser = cli.build_parser()
    args = parser.parse_args(
        ["run", "--product", "a tool", "--platforms", "x,instagram"]
    )
    rc = args.func(args, Config(env={"ANTHROPIC_API_KEY": "k"}))
    out = capsys.readouterr().out
    assert rc == 0
    assert "hook line" in out
    assert "Hook Simulation" in out
    assert "70/100" in out


def test_missing_credential_returns_exit_1(capsys):
    # `generate` with no key should surface a clean error, not a traceback.
    rc = cli.main(["--env", "/nonexistent.env", "generate", "--product", "x", "--platform", "x"])
    assert rc == 1
