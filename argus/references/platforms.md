# Installing per agent

The same `SKILL.md` folder is used everywhere. The folder name must match the `name` field (`argus`). Web and shell access depend on the product and your account.

| Agent | User scope | Project scope |
|---|---|---|
| OpenCode | `~/.config/opencode/skills/argus/` | `.opencode/skills/argus/` (also reads `.claude/skills/` and `.agents/skills/`) |
| Claude Code | `~/.claude/skills/argus/` | `.claude/skills/argus/` |
| OpenAI Codex | `~/.codex/skills/argus/` (`$CODEX_HOME/skills`) | `.agents/skills/argus/` |
| Hermes | `~/.hermes/skills/argus/` | n/a |
| Claude.ai | Upload a ZIP whose root contains the `argus/` folder (`make zip`) where custom skills are available. | n/a |
| ChatGPT | Sidebar > **Plugins** > **Skills** tab > **Create** > **Upload from your computer** (upload the ZIP from `make zip`). | n/a |

## ChatGPT

ChatGPT supports Agent Skills (checked against OpenAI's help center, October 2026). After upload, ChatGPT scans the skill; it may be marked **Needs Review** (you confirm) or **Blocked**. Then invoke it with `@argus` in a chat, or let ChatGPT pick it from the description.

- Availability depends on your plan and workspace settings: the help center lists Business, Enterprise, Healthcare and Edu, and says standalone skills work in the ChatGPT desktop app. If you do not see **Skills**, your plan or workspace may not have it (admins control upload permission).
- Fallback when skills are unavailable: paste `SKILL.md` into a Project's instructions and attach the `references/` files, then ask the chat to follow them. Script execution then depends on the tools you have enabled.

## Other agents

If the agent supports Agent Skills, point it at the folder as its docs describe. If not, supply `SKILL.md` as context. Not all behavior carries over.
