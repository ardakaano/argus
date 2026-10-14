# How to install and use Argus

Step by step, per platform. 🇹🇷 [Türkçe](HOWTO.tr.md)

Checked against each vendor's own documentation in October 2026 (links at the bottom). Menus and paths change, so if a step doesn't match what you see, trust the vendor's page. I did not run an upload on ChatGPT or Claude.ai myself; those steps come from their help centers.

## Before you start

You need the skill folder: the inner `argus/` directory of this repo (the one that contains `SKILL.md`).

```bash
git clone https://github.com/ardakaano/argus.git
cd argus
```

For ChatGPT and Claude.ai you upload a ZIP instead of copying a folder:

```bash
make zip        # creates argus-skill.zip with the argus/ folder at its root
```

Pick your platform:

| I use | Go to |
|---|---|
| OpenCode | [OpenCode](#opencode) |
| Claude Code | [Claude Code](#claude-code) |
| Codex (CLI or IDE) | [OpenAI Codex](#openai-codex) |
| Hermes | [Hermes](#hermes) |
| ChatGPT | [ChatGPT](#chatgpt) |
| Claude.ai | [Claude.ai](#claudeai) |

## The 30-second test (every platform)

After installing, send this:

```text
Argus: give me a quick launch plan for a tiny habit-tracker app.
```

The skill is working if the answer:

- says near the top that it is **hypothesis-only** because you gave no URL, and offers to research if you send one,
- has a section **against the plan** with **kill criteria**,
- gives a **48-hour experiment** and a draft post marked as not yet sent,
- does not invent sources, prices or conversion numbers.

If you get a generic marketing checklist instead, the skill did not load. See the troubleshooting line in your platform's section.

---

## OpenCode

**Install**

```bash
mkdir -p ~/.config/opencode/skills
cp -R argus ~/.config/opencode/skills/
```

Only for one project: copy it to `.opencode/skills/argus` in that project instead. OpenCode also reads `~/.claude/skills`, `~/.agents/skills`, `.claude/skills` and `.agents/skills`, so a copy placed for Claude Code or Codex is found too.

**Use it**

```text
@argus Audit https://example.com for indie SaaS founders, $300 budget.
```

Mentioning `@argus` loads it yourself. OpenCode can also pick it from the description.

**Update**: `git pull`, then replace the copy: `rm -rf ~/.config/opencode/skills/argus && cp -R argus ~/.config/opencode/skills/`.
**Remove**: delete that folder.

**If it does not show up**: the skill ID is the folder name and is case-sensitive, so the folder must be `argus`. Check that a later source does not define the same ID, and that your agent's `skill` permission is not `deny`.

---

## Claude Code

**Install**

```bash
mkdir -p ~/.claude/skills
cp -R argus ~/.claude/skills/
```

For one repository (shared with your team through git): `.claude/skills/argus`. To get updates with `git pull` and no re-copying, link it instead: `ln -s "$PWD/argus" ~/.claude/skills/argus`.

**Check**: run `/skills`. Argus should be listed. Claude Code picks up changes without a restart; if `~/.claude/skills/` did not exist when the session started, run `/reload-skills`.

**Use it**

```text
/argus Audit https://example.com for indie SaaS founders, $300 budget.
```

Or just ask in plain words; Claude loads it when the request matches.

**Update**: pull and re-copy (or nothing, if you linked it). **Remove**: delete `~/.claude/skills/argus/`.

**If it does not show up**: `/doctor` checks your setup. The frontmatter must start on the first line of `SKILL.md`. If you also uploaded Argus to claude.ai and signed in with the same account, a synced copy appears under `claude.ai sync`.

---

## OpenAI Codex

**Install**

```bash
mkdir -p ~/.agents/skills
cp -R argus ~/.agents/skills/
```

For one repository: `.agents/skills/argus`. Codex scans from your working directory up to the repo root.

**Check and use**: run `/skills` (or type `$`) and pick `argus`, or mention it:

```text
$argus Audit https://example.com for indie SaaS founders, $300 budget.
```

Codex also picks it from the description. It detects new skills automatically; if one does not appear, restart Codex.

**Update**: re-copy. **Remove**: delete the folder.

---

## Hermes

**Install**

```bash
mkdir -p ~/.hermes/skills
cp -R argus ~/.hermes/skills/
```

**Check**: `hermes skills list | grep argus`, or `/skills` in a chat. A new skill is available in **new** sessions; use `/reset` to start fresh right now.

**Use it**

```text
/argus Audit https://example.com for indie SaaS founders, $300 budget.
```

Every installed skill is a slash command, and you can also ask Hermes in plain words to use it.

**Update**: re-copy. **Remove**: delete the folder.

Hermes can also install from a URL (`hermes skills install <url-to-SKILL.md>`, per its docs). I did not test that with this repo, so the copy method above is the reliable one.

---

## ChatGPT

Skills in ChatGPT are available to eligible Business, Enterprise, Healthcare and Edu plans, and standalone skills work in the ChatGPT desktop app. If you do not see **Skills**, your plan or workspace may not have it, or an admin may have turned uploads off.

**Install**

1. Run `make zip`.
2. In ChatGPT's sidebar choose **Plugins**, then the **Skills** tab.
3. Choose **Create**, then **Upload from your computer**, and pick `argus-skill.zip`.
4. ChatGPT scans the upload. If it says **Needs Review**, read what it shows and confirm. **Blocked** means it cannot be used.

**Use it**: type `@` and pick `argus`, or just ask; ChatGPT can choose it from the description.

```text
@argus Audit https://example.com for indie SaaS founders, $300 budget.
```

**Update**: upload the new ZIP. **Remove**: delete it from the Skills page.

**No Skills on your plan?** Paste `SKILL.md` into a Project's instructions and attach the `references/` files, then start with "Follow the Argus instructions". The skill itself still works, but script runs depend on the tools you have enabled.

---

## Claude.ai

Available on Free, Pro, Max, Team and Enterprise. It needs **Code execution and file creation** turned on (Settings > Capabilities; on Team and Enterprise an owner enables it in Organization settings > Plugins & skills).

**Install**

1. Run `make zip`. The ZIP's root must be the `argus/` folder, which this builds.
2. Open **Customize > Skills**.
3. Click **+**, then **Create skill**, then **Upload a skill**, and pick `argus-skill.zip`.
4. Switch the skill **on**.

**Use it**: ask explicitly the first time.

```text
Use my Argus skill to audit https://example.com for indie SaaS founders, $300 budget.
```

**Update**: upload the new ZIP. **Remove**: open the skill, switch it off, then use "..." > Delete. If you use Claude Code with the same account, enabled skills sync there too.

**If the upload fails**: the help center lists these causes: ZIP too large, folder name not matching the skill name, missing `SKILL.md`, invalid characters in the name or description. One thing to watch: Anthropic's "How to create custom skills" article still says descriptions are limited to 200 characters, while the Agent Skills spec allows 1024. Argus's description is about 590 characters. If yours is rejected for length, shorten the `description` line in `SKILL.md` to about 200 characters and keep the Turkish trigger phrases.

---

## Optional: the report script

Argus can save its findings as JSON and render them as markdown or a one-file HTML report. It needs Python 3.10+ and nothing else. Agents with a shell (OpenCode, Claude Code, Codex, Hermes, and ChatGPT or Claude.ai with code execution) run it for you in Full mode. By hand:

```bash
python3 argus/scripts/render_report.py --template > findings.json
python3 argus/scripts/render_report.py findings.json --check --strict
python3 argus/scripts/render_report.py findings.json -o plan.html
```

## Good to know

- **Argus researches only when you give it a URL.** With your URL it researches and cites sources with dates. Without one it does no search or fetch at all, even if your agent has web tools, and gives a hypothesis-only plan with an offer to research once you send the link.
- **Quick or Full**: a short question gets a short answer. Ask for a "plan", "audit" or "30-day" for the full version.
- **Nothing is sent for you.** Posts, emails and DMs are drafts you approve.
- **Language**: it answers in the language you write in.

## Sources

- OpenCode V2 skills: https://opencode.ai/v2/docs/skills/
- Claude Code skills: https://code.claude.com/docs/en/skills
- OpenAI, build skills (ChatGPT and Codex): https://learn.chatgpt.com/docs/build-skills
- OpenAI, skills in ChatGPT: https://help.openai.com/en/articles/20001066-skills-in-chatgpt
- Hermes, working with skills: https://hermes-agent.nousresearch.com/docs/guides/work-with-skills
- Claude help center, use skills: https://support.claude.com/en/articles/12512180-use-skills-in-claude
- Claude help center, create custom skills: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
