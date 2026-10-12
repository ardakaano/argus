# Installing per agent

The same `SKILL.md` folder is used everywhere. The folder name must match the `name` field (`argus`). Web and shell access depend on the product and your account.

| Agent | User scope | Project scope |
|---|---|---|
| OpenCode | `~/.config/opencode/skills/argus/` | `.opencode/skills/argus/` (also reads `.claude/skills/` and `.agents/skills/`) |
| Claude Code | `~/.claude/skills/argus/` | `.claude/skills/argus/` |
| OpenAI Codex | `~/.codex/skills/argus/` (`$CODEX_HOME/skills`) | `.agents/skills/argus/` |
| Hermes | `~/.hermes/skills/argus/` | n/a |
| Claude.ai | Upload a ZIP whose root contains the `argus/` folder (`make zip`) where custom skills are available. | n/a |

## ChatGPT (ordinary chats)

Chats do not natively install local skills. Upload the files or paste `SKILL.md` into a Project's instructions, and ask the chat to follow them. File references and script execution depend on enabled tools.

## Other agents

If the agent supports Agent Skills, point it at the folder as its docs describe. If not, supply `SKILL.md` as context. Not all behavior carries over.
