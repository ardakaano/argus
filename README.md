# Argus 👁️

**A hundred eyes on your launch.**

In Greek myth, Argus Panoptes was the watcher with a hundred eyes, and some of them were always awake. This Agent Skill gives your AI agent the same habit for launching a SaaS, app or indie product: look at the product, customers, competitors, communities and channels together, and keep one eye open for evidence that your plan is wrong.

Your product needs a distribution strategy, not another launch checklist. Argus picks three channels instead of fifteen, shows its sources, and says what it could not verify.

> Status: **v0.2.0**. Research is done by your agent with its own web tools. This repo has no crawler, no community-discovery API and no posting automation. The optional script only validates and renders JSON. 🇹🇷 [Türkçe README](README.tr.md)

## What you get

- Product and positioning audit
- Primary and secondary ideal customers
- Competitor and community research with an **evidence ledger** (source URL + access date)
- **Disconfirming evidence and kill criteria**, so the plan can be wrong in public
- Weighted channel ranking that never recommends promotion where it's banned
- 30-day sprint with weekly stop/go gates
- Draft positioning, three hooks, a launch post and a non-spammy reply
- Five measurable experiments, at least one startable within 48 hours

Two modes: **Quick** (one screen) and **Full** (everything above). Replies in your language.

## Install

The folder name must match the skill name (`argus`).

| Agent | Command |
|---|---|
| OpenCode | `mkdir -p ~/.config/opencode/skills && cp -R argus ~/.config/opencode/skills/` |
| Claude Code | `mkdir -p ~/.claude/skills && cp -R argus ~/.claude/skills/` |
| OpenAI Codex | `mkdir -p ~/.agents/skills && cp -R argus ~/.agents/skills/` |
| Hermes | `mkdir -p ~/.hermes/skills && cp -R argus ~/.hermes/skills/` |
| Claude.ai | `make zip`, then upload `argus-skill.zip` where custom skills are available |

Project-scoped locations and ChatGPT notes are in [`argus/references/platforms.md`](argus/references/platforms.md).

## Use

```text
/argus Analyze https://example.com for a US/UK market and a $300 launch budget.
/argus I have a micro-SaaS onboarding analytics tool. Help me find my first 20 users.
/argus Compare our positioning against credible competitors; show sources and dates.
/argus Web yok: B2B takvim uygulaması için hipotez odaklı bir lansman planı hazırla.
```

Without web access, Argus produces a clearly labeled **hypothesis-only** plan. It does not pretend to have audited your URL.

## Optional report renderer

Python 3.10+, no dependencies. Your agent saves its findings as JSON, and the script validates and renders them:

```bash
python3 argus/scripts/render_report.py --template > findings.json       # skeleton
python3 argus/scripts/render_report.py findings.json -o plan.md          # render
python3 argus/scripts/render_report.py findings.json --lang tr           # Turkish headings
python3 argus/scripts/render_report.py findings.json --check --strict    # quality gate only
```

It rejects malformed findings (for example, a "verified" claim without a URL and date), warns about quality-gate gaps, and neutralizes pipes, newlines and raw HTML in text that came from the web. See [`report-format.md`](argus/references/report-format.md).

Sample output: [`example-report.md`](argus/examples/example-report.md) (English) and [`example-report.tr.md`](argus/examples/example-report.tr.md) (Türkçe). The product in both is fictional.

## Layout

```text
argus/                        ← repo
├── argus/                    ← the skill (copy this folder)
│   ├── SKILL.md
│   ├── references/           research, scoring, experiments, copywriting, report-format, platforms
│   ├── assets/report-template.md
│   ├── scripts/render_report.py
│   └── examples/             input/output JSON (en, tr) and rendered reports
├── tests/test_render.py
├── Makefile                  test | examples | zip
└── .github/workflows/test.yml
```

## Develop

```bash
make test       # 43 tests, stdlib only
make examples   # regenerate rendered examples (a test checks they are in sync)
```

## Roadmap

- [x] Vendor-neutral Agent Skills instructions
- [x] Evidence, safety and disconfirmation protocol
- [x] Validating, localized renderer with lint and CI
- [ ] Real-world evaluation on several products and languages
- [ ] Optional approved source adapters with caching and rate limits
- [ ] Opt-in recurring market signals (user approval required)

## Contributing

PRs welcome: scoring calibration, source verification, translations, install testing on more agents. Please don't contribute scraping that bypasses access controls, unsolicited mass messaging, or invented data.

## License

MIT. See [LICENSE](LICENSE).
