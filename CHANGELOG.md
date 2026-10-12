# Changelog

## 0.2.0

- Renamed from Launch Radar to **Argus** (the hundred-eyed watcher). The skill folder is now `argus/`.
- Skill: Quick and Full modes, a "doubt eye" step that looks for disconfirming evidence and defines kill criteria, Turkish trigger phrases, replies in the user's language.
- New references: `experiments.md`, `copywriting.md`, `report-format.md`. Rewrote `research.md`, `scoring.md`, `platforms.md` (added OpenCode).
- Renderer:
  - Structural validation that reports every problem at once; verified evidence needs an http(s) URL and an ISO date.
  - Quality-gate lint warnings (`--check`, `--strict`), including typo detection for unknown fields.
  - Channels that prohibit promotion (`promotion_allowed: false`) are never assigned a sprint role.
  - Integer scoring (no float rounding); same result as the documented formula.
  - ICPs, snapshot, disconfirming evidence, kill criteria, week gates and experiment budgets in the report.
  - English and Turkish output (`--lang`), `--template`, stdin input.
  - Untrusted text is neutralized (pipes, newlines, raw HTML) before it reaches the markdown.
- Examples: complete fictional English and Turkish reports, rendered; a test keeps them in sync.
- Tests grew from 4 to 43; CI on Python 3.10, 3.12 and 3.13; `make test | examples | zip`.

## 0.1.0

- First prototype as Launch Radar.
