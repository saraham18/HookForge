"""HookForge command-line interface."""
from __future__ import annotations

import argparse
import sys

from .config import Config, MissingCredential
from .generate import generate_post, supported_platforms
from .simulate import simulate

BANNER = "🔨 HookForge"


def _print_post(post) -> None:
    print(f"\n— {post.platform} ({post.char_count} chars) " + "-" * 30)
    print(post.text)


def _print_report(report) -> None:
    print(f"\n🎯 Hook Simulation — avg scroll-stop {report.average_score}/100")
    print(f"   Verdict: {report.verdict}\n")
    for r in report.reactions:
        name = r.persona.replace("_", " ").title()
        print(f"  [{r.scroll_stop_probability:>3}/100] {name}")
        print(f"        \"{r.monologue}\"")
        if r.biggest_flaw:
            print(f"        weakest link: {r.biggest_flaw}")
    print()


def cmd_generate(args, config: Config) -> int:
    post = generate_post(config, args.product, args.platform, tone=args.tone)
    _print_post(post)
    return 0


def cmd_simulate(args, config: Config) -> int:
    report = simulate(config, args.text, platform=args.platform)
    _print_report(report)
    return 0


def cmd_run(args, config: Config) -> int:
    """Generate for each platform, then stress-test each draft."""
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    for platform in platforms:
        post = generate_post(config, args.product, platform, tone=args.tone)
        _print_post(post)
        report = simulate(config, post.text, platform=platform)
        _print_report(report)
    print("Review the drafts above, then publish with `hookforge publish`.")
    return 0


def cmd_publish(args, config: Config) -> int:
    if args.platform == "x":
        from .publishers import publish_to_x

        result = publish_to_x(config, args.text)
    elif args.platform == "instagram":
        if not args.image_url:
            print("Instagram requires --image-url (a public https image URL).")
            return 2
        from .publishers import publish_to_instagram

        result = publish_to_instagram(config, args.text, args.image_url)
    else:
        print(f"Unknown platform: {args.platform}")
        return 2
    print(f"✅ Published to {args.platform}: {result['url']}")
    return 0


def cmd_card(args, config: Config) -> int:
    from .image import make_card

    path = make_card(args.headline, args.subtitle or "", args.out)
    print(f"🖼  Card written to {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hookforge", description=BANNER)
    parser.add_argument(
        "--env", default=".env", help="Path to .env file (default: .env)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plats = ", ".join(supported_platforms())

    g = sub.add_parser("generate", help="Generate one post for one platform")
    g.add_argument("--product", required=True, help="Brief: what you're promoting")
    g.add_argument("--platform", required=True, help=f"One of: {plats}")
    g.add_argument("--tone", help="Optional desired tone")
    g.set_defaults(func=cmd_generate)

    s = sub.add_parser("simulate", help="Stress-test a draft against cynical personas")
    s.add_argument("--text", required=True, help="The draft post text")
    s.add_argument("--platform", default="x", help=f"One of: {plats}")
    s.set_defaults(func=cmd_simulate)

    r = sub.add_parser("run", help="Generate + stress-test across platforms")
    r.add_argument("--product", required=True, help="Brief: what you're promoting")
    r.add_argument(
        "--platforms", default="x,instagram", help="Comma-separated platforms"
    )
    r.add_argument("--tone", help="Optional desired tone")
    r.set_defaults(func=cmd_run)

    p = sub.add_parser("publish", help="Publish a post (uses your API keys)")
    p.add_argument("--platform", required=True, help="x or instagram")
    p.add_argument("--text", required=True, help="The post/caption text")
    p.add_argument("--image-url", help="Public https image URL (Instagram only)")
    p.set_defaults(func=cmd_publish)

    c = sub.add_parser("card", help="Render a branded announcement image")
    c.add_argument("--headline", required=True)
    c.add_argument("--subtitle")
    c.add_argument("--out", default="card.png")
    c.set_defaults(func=cmd_card)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = Config.load(args.env)
    try:
        return args.func(args, config)
    except MissingCredential as exc:
        print(f"⚠️  {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # surface a clean error, not a traceback
        print(f"❌ {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
