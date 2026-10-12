# Installing per agent

Step-by-step instructions with checks and troubleshooting are in `HOWTO.md` at the repository root. This page is the short reference.

The same `SKILL.md` folder is used everywhere. The folder name must match the `name` field (`argus`). Web and shell access depend on the product and your account.

| Agent | User scope | Project scope |
|---|---|---|
| OpenCode | `~/.config/opencode/skills/argus/` | `.opencode/skills/argus/` (also reads `.claude/skills/` and `.agents/skills/`) |
| Claude Code | `~/.claude/skills/argus/` | `.claude/skills/argus/` |
| OpenAI Codex | `~/.codex/skills/argus/` (`$CODEX_HOME/skills`) | `.agents/skills/argus/` |
| Hermes | `~/.hermes/skills/argus/` | n/a |
| Claude.ai | **Customize > Skills** > "+" > **Create skill** > **Upload a skill**, then the ZIP from `make zip`. Toggle it on. | n/a |
| ChatGPT | Sidebar > **Plugins** > **Skills** tab > **Create** > **Upload from your computer** (upload the ZIP from `make zip`). | n/a |

## Claude.ai

Checked against Anthropic's help center, October 2026. Available on Free, Pro, Max, Team and Enterprise, and it needs **Code execution and file creation** switched on (Settings > Capabilities; on Team and Enterprise an owner enables it under Organization settings > Plugins & skills). The ZIP must contain the skill folder as its root, which is what `make zip` builds. After uploading, toggle the skill on and try an explicit prompt ("Use my Argus skill to audit ..."). Skills you enable also sync to Claude Code when you are signed in with the same account.

If an upload fails, the help center lists these causes: ZIP too large, folder name not matching the skill name, missing `SKILL.md`, invalid characters in the name or description. One thing to watch: Anthropic's "How to create custom skills" article still says the description is limited to 200 characters, while the Agent Skills spec allows 1024. Argus's description is about 490 characters. I could not test an upload; if yours is rejected for length, shorten the `description` line in `SKILL.md` to about 200 characters and keep the Turkish trigger phrases.

## ChatGPT

ChatGPT supports Agent Skills (checked against OpenAI's help center, October 2026). After upload, ChatGPT scans the skill; it may be marked **Needs Review** (you confirm) or **Blocked**. Then invoke it with `@argus` in a chat, or let ChatGPT pick it from the description.

- Availability depends on your plan and workspace settings: the help center lists Business, Enterprise, Healthcare and Edu, and says standalone skills work in the ChatGPT desktop app. If you do not see **Skills**, your plan or workspace may not have it (admins control upload permission).
- Fallback when skills are unavailable: paste `SKILL.md` into a Project's instructions and attach the `references/` files, then ask the chat to follow them. Script execution then depends on the tools you have enabled.

## Other agents

If the agent supports Agent Skills, point it at the folder as its docs describe. If not, supply `SKILL.md` as context. Not all behavior carries over.
