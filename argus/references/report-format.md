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
| `icps` | array | Items: `name`, `primary` (bool), `job_to_be_done`, `trigger`, `alternatives`, `objections`. |
| `evidence` | array | Items: `claim`, `status` (`verified`/`inference`/`hypothesis`), `confidence` (`high`/`medium`/`low`), `source_url`, `accessed_on`. `verified` requires an http(s) URL and a date. |
| `disconfirming` | array of strings | Evidence or open questions against the leading hypothesis. |
| `channels` | array | Items: `name`, `scores` (all seven keys, integers 1–5), `rationale`, `effort`, `rule`, `promotion_allowed` (bool, default true), `basis` (`evidence`/`assumption`). |
| `weeks` | array | Items: `week` (int), `objective`, `actions` (strings), `signal`, `gate`. |
| `copy` | object | `positioning`, `hooks` (array), `launch_post`, `reply_draft`. |
| `experiments` | array | Items: `hypothesis`, `channel`, `test`, `kpi`, `decision_gate`, `budget_usd`, `within_48h` (bool). |
| `risks` | array of strings | |
| `kill_criteria` | array of strings | |
| `next_action` | string | |

## Warnings the renderer may print

- Fewer than 3 or more than 8 channels.
- Fewer than 2 channels eligible for promotion.
- Not exactly 4 weeks, or a week without a gate.
- Not exactly 3 hooks, or not exactly 5 experiments.
- No experiment marked `within_48h`.
- No `disconfirming` entries or `kill_criteria`.
- Live mode with no evidence, or without `accessed_on`.
- A top channel scored mostly on assumptions (`basis: assumption`) in live mode.
- Missing `next_action`.

Text is placed in markdown tables and lists after newlines and pipes are neutralized. The renderer fetches nothing.
