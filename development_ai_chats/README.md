# Development AI Conversations

Every AI conversation used to build this project, as required by the assignment. User prompts and
model answers/actions are clearly separated.

| File | Tool | Content |
|---|---|---|
| `01-claude-code-main-session.md` | Claude Code (Claude Opus) | The whole development session: planning (including the user's comparison with a Gemini-generated plan, quoted in the first prompts), backend (TDD), Docker, frontend coordination, testing strategy, live LLM evaluation, page numbers verified against Microsoft Word, Agent Skill, architecture docs |
| `02-subagent-frontend-builder.md` | Claude Code subagent (`senior-front-developer`) | The React frontend, delegated by the main session; the first section is the orchestrator's brief, later sections are follow-up requests |
| `03-subagent-skill-tester.md` | Claude Code subagent (general-purpose) | An independent test of the Agent Skill, deliberately run without access to the ground truth or the backend code |

## How to read the files

- `## USER`: a prompt typed by the developer. `## USER (slash command)`: a Claude Code command such as `/model` or `/chrome`.
- `## CLAUDE`: the model's reply. `**Tool call: X**` blocks show each action (shell command, file write or edit, browser step) with its input; the collapsible `Result:` below each one holds the (truncated) output.
- `## SUBAGENT REPORT (to Claude)`: a subagent's final report delivered to the main session. `## SYSTEM NOTIFICATION`: background-task events from the tool.
- `## CLAUDE (orchestrator) TO SUBAGENT`: the brief a subagent received.

## How they were produced

Exported from Claude Code's session transcripts (JSONL) into Markdown with a small converter. For a
public repository:
- The model's internal reasoning blocks and the tool's injected system context (organization
  standards, git status, reminders) are omitted.
- The developer's email address, name and home-folder path are redacted (`[redacted]`, `<home>`).
- Long tool inputs and outputs are truncated, with the full size noted.
- No API key appears anywhere: the real key value from `.env` was searched for in every transcript
  and every repository file before export (zero matches).

The planning-stage conversation with Gemini is quoted inside the first prompts of
`01-claude-code-main-session.md`.
