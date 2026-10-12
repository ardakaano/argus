# Research protocol

Use live browsing when available. Prefer original evidence: official product pages, official pricing, primary discussions, current platform guidelines, firsthand users. Mark secondary commentary as secondary.

## Search patterns

- Product: official features, pricing, integrations, changelog, customers, docs.
- Alternatives: `[category] alternatives`, `[competitor] vs`, `[problem] workaround`, `[problem] spreadsheet`.
- Friction: `site:reddit.com [problem]`, `site:news.ycombinator.com [problem]`, GitHub issues labeled feature request, app-store reviews of incumbents.
- Disconfirmation: `[category] is dead`, `why I stopped using [competitor]`, `free alternative to [category]`, `[category] not worth it`.
- Discovery: relevant newsletters, directories, communities, integration marketplaces.
- Access: read the community's *current* self-promotion and participation rules before proposing any post.

## Evidence ledger

For each claim record:

| Field | Values |
|---|---|
| `claim` | One concrete statement. |
| `status` | `verified`, `inference` or `hypothesis`. |
| `confidence` | `high`, `medium` or `low`. |
| `source_url` | A real `http(s)` URL you actually opened. Required when `verified`. |
| `accessed_on` | `YYYY-MM-DD`. Required when `verified`. |

Do not label a claim `verified` unless you saw reliable evidence yourself. Never invent a URL.

## Distinctions

- A pain-point mention is not proof of purchase intent.
- High engagement is not proof of conversion.
- A community's relevance is not permission to post.
- Competitor marketing claims are not independently verified performance.
- A public price may be regional, discounted or stale.
- One loud thread is an anecdote. Look for the same pain in at least three independent places before calling it a pattern.

## Source freshness

Community rules, prices and rankings change. Re-read them on the day you plan to act, and show the access date in the report.

## No browsing

Set `research_mode` to `hypothesis-only` and keep the evidence ledger empty rather than manufacturing evidence. Hypotheses are still useful: they tell the user what to verify first.
