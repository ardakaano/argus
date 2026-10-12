# Report JSON format

`scripts/render_report.py` turns a findings JSON into a markdown report. Get a skeleton with:

```bash
python3 scripts/render_report.py --template > findings.json
```

Fields marked **required** cause an error if missing or invalid. Everything else is optional; gaps in the quality gate are reported as warnings (use `--strict` to make them errors).

| Field | Type | Notes |
|---|---|---|
| `product_name` | string, **required** | |
| `research_mode` | `"live"` \| `"hypothesis-only"`, **required** | `hypothesis-only` forbids evidence entries. |
| `accessed_on` | `YYYY-MM-DD` | Expected when `research_mode` is `live`. |
| `language` | `"en"` \| `"tr"` | Heading language. `--lang` overrides it. Default `en`. |
| `market` | string | |
| `summary` | string | The verdict. |
| `biggest_uncertainty` | string | |
| `snapshot` | object | Any of `problem`, `promise`, `stage`, `pricing`, `cta`, `differentiation`. |
| `audit_findings` | array of strings | Defects or fixes found on the product's own pages (clarity, CTA, proof, pricing). |
| `icps` | array | Items: `name` (do not add "(primary)" yourself; the renderer does), `primary` (bool), `job_to_be_done`, `trigger`, `alternatives`, `objections`. |
| `evidence` | array | Items: `claim`, `status` (`verified`/`inference`/`hypothesis`), `confidence` (`high`/`medium`/`low`), `source_url`, `source_type` (`primary`/`secondary`/`snippet`), `accessed_on`, `note` (for example a conflict between sources). `verified` requires an http(s) URL and a date. |
| `assumptions` | array of strings | How you read the request, what you took for granted. |
| `limits` | array of strings | What you could not access or check (blocked pages, login walls, no web). |
| `disconfirming` | array of strings | Evidence or open questions against the leading hypothesis. |
| `channels` | array | Items: `name`, `scores` (all seven keys, integers 1–5), `rationale`, `effort`, `rule`, `promotion_allowed` (`true`, `false` or `"unknown"`; default true), `basis` (`evidence`/`assumption`). |
| `budget_plan` | array of strings | What is spent now, what is conditional on which result, what stays in reserve. |
| `weeks` | array | Items: `week` (int), `objective`, `actions` (strings), `signal`, `gate`. |
| `copy` | object | `positioning`, `hooks` (array), `launch_post`, `reply_draft`, `outreach_draft` (a one-to-one message asking for a conversation). |
| `experiments` | array | Items: `hypothesis`, `channel`, `test`, `kpi`, `decision_gate`, `budget` (free text in any currency, for example `"500 TL"`; wins over `budget_usd`), `budget_usd` (number), `within_48h` (bool). |
| `risks` | array of strings | |
| `kill_criteria` | array of strings | |
| `next_action` | string | |

## Output

```bash
python3 scripts/render_report.py findings.json -o report.md     # markdown
python3 scripts/render_report.py findings.json -o report.html   # one self-contained HTML page
python3 scripts/render_report.py findings.json --lang tr        # Turkish headings
```

The HTML has inline CSS only: no scripts, no external requests, a restrictive Content-Security-Policy. It follows the system light or dark theme and prints cleanly. Every field is HTML-escaped.

Channel roles: the top two promotable channels with `speed` of 3 or more are "Validate now", the next is "After checkpoint", the rest "Later". Channels with `speed` of 2 or less are "Background (slow payoff)". Channels with `promotion_allowed: false` are "Participate only"; `"unknown"` shows "Read the rules first" and also cannot take a sprint slot. In hypothesis-only mode the report adds one note that all scores are assumptions instead of tagging every row.

## Notes and warnings

`note:` lines are information the renderer cannot make you clear (a channel's rules are unknown, a top channel rests on assumptions, fewer than two promotable channels can show a signal within weeks). They never fail `--strict`. `warning:` lines are quality-gate gaps you can always fix; `--strict` fails on them.

Evidence you saw only in a search snippet or a summary: set `status: "inference"`, `source_type: "snippet"` or `"secondary"`, and leave `source_url` out unless you opened it.

## Warnings the renderer may print

- Fewer than 2 or more than 8 channels.
- Not exactly 4 weeks, or a week without a gate.
- Not exactly 3 hooks, or not exactly 5 experiments.
- No experiment marked `within_48h`.
- No `disconfirming` entries or `kill_criteria`.
- Live mode with no evidence, or without `accessed_on`.
- Missing `next_action`.

Text is placed in markdown tables and lists after newlines and pipes are neutralized. The renderer fetches nothing.
