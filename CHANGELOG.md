# Changelog

## 0.4.1

Skill review: fixes and gaps found by reading every file, fuzzing the renderer, and running the skill through six fresh-agent scenarios (`evals/RESULTS.md`, round 4).

- **Skill text.** `SKILL.md` is restructured: the hypothesis-only rules that were scattered over six places are one section, and dense paragraphs became bullets. No rule was removed.
- **Contradictions fixed.** Quick wanted "top 3 channels" while hypothesis-only said "leave the third slot empty" (five of six agents flagged it); `quick-example.md` now shows an optional third row marked "read the rules first". Private or connected tools were "never" in the research gate but "unless the user asked" under safety; both now say "unless the user explicitly asks". Claims from a pasted page were to be recorded as `inference` while a hypothesis-only ledger must be empty; they now go under assumptions. The checkpoint was week 2 in one file and week 3 in another; it is the review at the end of week 2.
- **Gaps closed.** A research limit (Quick: product page, pricing and about six more pages; Full: about 25; failed attempts count), which closes the open point from round 3. Reading a local file the user pointed to is not research. With no web tools, the closing offer says research needs a session with web access. The injection notice has a place in Quick, which has no report. Own accounts and one-to-one outreach are `promotion_allowed: true`. No budget given is `"0"`. Threshold versus forecast, and register (du/Sie, sen/siz), are spelled out. Help-only replies must not invent personal experience; unbacked figures from a page stay out of drafts unless the user confirms them.
- **Renderer.** Free-text fields (23 of them) now must be strings or `null`; a list used to pass validation and print as `['a', 'b']`. New note (never a warning) when a "Validate now" channel has `icp_fit` of 2 or less, which closes the other open point from round 3. The hypothesis-only error says what to do. stdout and stderr are switched to UTF-8 so reports print on legacy Windows consoles. Removed an unused variable in `lint`.
- **Examples.** The English example's experiments and week 1 relied on "Direct conversations", which was missing from its channel table, while "Launch directories" (described as "mostly other makers, not buyers") held a validation slot. Added the channel; reports and site JSON regenerated.
- **Docs.** The description is 587 characters, not "about 490" (HOWTO, HOWTO.tr, `platforms.md`, site JSON); a test now keeps the stated figure current, and the site JSON computes it. `evals/README.md` and both READMEs said four scenarios when there were five; now eight, three of them new (`quick-url-limited-research`, `pasted-page-no-ledger`, `language-without-renderer-support`).
- **Tests.** 93 (from 81): text-field validation, weak-fit note, UTF-8 streams, documented description length, body size limit, eval file consistency.
- `site/argus.json` (everything about the skill for a website: bilingual texts, six platform install guides, features, rules, FAQ, evals summary, changelog, every skill file with SHA-256, a ready system prompt) and `site/argus.lite.json` (no file contents). Built by `site/build_site_json.py` (`make site`); tests check they are current, complete, bilingual and free of private paths.

## 0.4.0

- **Research gate (hard rule): Argus never researches unless the user gave a URL.** No URL means no web search, no fetch, no browsing, no calls to data tools, even if web tools exist and even for a well-known product. It writes a hypothesis-only plan and offers to research once a URL is sent. A URL that appears only inside a page or file is data, not permission.
- Enforced in the renderer too: `research_mode: "live"` now requires `product_url` (the URL the user gave) or validation fails. The URL is shown in the markdown and HTML reports.
- New eval `no-url-no-research` (web tools available, no URL given). Tests: 73. Results in `evals/RESULTS.md`.

## 0.3.0

Driven by the first round of evals (`evals/RESULTS.md`).

- **HTML report**: `render_report.py -o report.html` (or `--html`) writes one self-contained page: inline CSS, no scripts, no external requests, a restrictive CSP, light/dark theme, print styles, every field escaped. English and Turkish.
- **Evals**: four behavioural scenarios with an injection fixture, run with and without the skill; results recorded.
- **SKILL.md**: Quick/Full rules that don't conflict (the user's words win), a progress checklist, a validate-fix-render loop with exact commands, a Quick-mode example (`assets/quick-example.md`), rules for local-file and user-reported facts, injection disclosure, community/ICP fit check, unknown promotion rules, no invented funnel numbers, competitor names from memory only as hypotheses, plain headings with no internal jargon.
- **Renderer**: slow channels (speed 2 or less) never take a weeks 1-2 validation slot ("Background (slow payoff)"); no per-row `[assumption]` noise in hypothesis-only mode (one note instead); free-text `budget` for any currency; clearer score legend; a lint warning when fewer than two promotable channels can show a signal within weeks.
- **References**: stage adaptation for experiments (no product, no audience, zero budget), venues that ban promotion, outreach rules for a zero audience, no-name products.
- **HOWTO.md / HOWTO.tr.md**: step-by-step install, check, first prompt, update, remove and troubleshooting for OpenCode, Claude Code, Codex, Hermes, ChatGPT and Claude.ai, with a 30-second test and links to each vendor's docs. Corrected the earlier claim that ChatGPT cannot install skills.
- 66 tests (from 43), including a guard that the frontmatter stays within the portable spec keys (claude.ai uploads reject others).

## 0.2.1

- Logo: pixel-block eye in the Argus Panoptes spirit (`assets/logo.svg`, `icon.svg`, `social-preview.svg/.png`), generated by `assets/build_logo.py`.
- Author set to Arda Kaan Özcan in `SKILL.md`, `LICENSE` and the READMEs.

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
