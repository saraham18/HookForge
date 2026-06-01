# HookForge

**Generate scroll-stopping social posts, stress-test them against cynical reader
personas, and publish to X + Instagram - bring your own API keys.**

Most social tools help you *schedule* posts. None of them tell you the thing that
actually matters: **why a fast scroller would scroll right past your hook.**
HookForge does. It runs every draft past three blunt, cynical personas before you
publish, scores the scroll-stop probability, and points at the weakest line.

No SaaS account. No data leaves your machine. You plug in your own keys.

---

## Why this exists

In 2026, the marketing bottleneck moved. Writing copy is cheap - LLMs do it in
seconds. The hard part is knowing whether a hook will *stop the scroll* in a feed
that punishes links and rewards native, zero-click content. Marketers are stuck
guessing which headline works, and generic AI copy gets penalized for sounding
like a press release.

HookForge attacks that gap directly with the **Zero-Click Hook Simulator**: three
distinct, cynical personas react to your draft the way real people think but never
say out loud.

| Persona | What they punish |
|---|---|
| **The Tired Developer** | hype, buzzwords, anything without substance |
| **The Hurried Executive** | slow setups, no clear outcome or number |
| **The Gen-Z Marketer** | corporate speak, cringe, press-release energy |

Each returns an unvarnished internal monologue, a **scroll-stop probability
(0-100)**, and the single weakest link in your hook. You get a verdict before you
ever hit publish.

---

## Install

```bash
git clone https://github.com/saraham18/HookForge.git
cd HookForge
pip install -e ".[all]"        # or pick extras: ".[generate,x]"
cp .env.example .env           # then fill in your keys
```

Core logic and the full test suite run with **zero dependencies** - the SDKs
(`anthropic`, `tweepy`, `requests`, `Pillow`) are imported lazily and only needed
for the features you actually use.

## Configure

Everything is bring-your-own-keys via `.env` (gitignored - keys never get
committed). See [`.env.example`](.env.example):

- `ANTHROPIC_API_KEY` - for `generate` / `simulate` / `run`
- `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` - to publish to X
- `IG_ACCESS_TOKEN`, `IG_USER_ID` - to publish to Instagram

## Use

```bash
# Generate + stress-test posts across platforms (the main loop)
hookforge run --product "An open-source AI marketing copilot that critiques your
hooks before you publish" --platforms x,instagram

# Just stress-test a draft you already wrote
hookforge simulate --text "We built an AI tool game changer" --platform x

# Generate one post
hookforge generate --product "..." --platform x --tone "dry and confident"

# Target a specific audience and follow a brand guide (a file path or inline text).
# With --audience, the simulator builds personas matching that demographic instead
# of the default trio. --brand accepts a brand-guide.json produced by BrandForge.
hookforge run --product "..." --audience "fitness founders, 30-45" --brand brand-guide.json

# Make a branded 1080x1080 image card (Instagram needs an image)
hookforge card --headline "We just shipped" --subtitle "v0.1 is live" --out docs/card.png

# Publish (uses your keys)
hookforge publish --platform x --text "..."
hookforge publish --platform instagram --text "..." --image-url "https://.../card.png"
```

### Example: the hook simulator

```
$ hookforge simulate --text "We built an AI tool game changer" --platform x

Hook Simulation - avg scroll-stop 22.3/100
   Verdict: WEAK - rewrite the hook before publishing

  [ 15/100] Tired Developer
        "'Game changer' with a rocket emoji - instant skip, zero substance."
        weakest link: no concrete claim
  ...
```

> Instagram's API can't post text-only - it fetches a **public** image URL
> server-side. Handy trick: commit your card to a public repo and pass its
> `raw.githubusercontent.com` URL to `--image-url`.

## Architecture

```
hookforge/
config.py        # bring-your-own-keys, .env loader, credential checks
llm.py           # thin Anthropic Messages wrapper (lazy import, injectable)
generate.py      # platform-native post generation (X / Instagram / LinkedIn)
simulate.py      # the Zero-Click Hook Simulator (cynical personas)
image.py         # branded announcement card (Pillow)
publishers/
  x.py         # X API v2 via Tweepy
  instagram.py # Meta Graph API two-step publish
cli.py           # argparse CLI: generate / simulate / run / publish / card
```

Every LLM and network call is **injectable**, so the whole thing is unit-tested
offline with fakes - no keys, no network:

```bash
pip install pytest && pytest -q     # 17 passing
```

## Contributing

Issues and PRs welcome. Good first additions: more platforms (`PLATFORMS` in
`generate.py`), more personas (`PERSONAS` in `simulate.py`), or a scheduler.

## License

MIT © 2026 Sarah McLellan
