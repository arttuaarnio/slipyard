---
name: skills
description: Show, add or remove the skills Slipyard's agents load - orchestrator, planner, builder, reviewers - for this project or for every project.
argument-hint: "[--global] [<agent> add|remove <skill>...]"
disable-model-invocation: true
---

# Slipyard: manage agent skills

Arguments: $ARGUMENTS

Slipyard works without any skills. Skills let the user shape how each agent works: a design skill for the builder, a security checklist for the security reviewer, a house style for specs.

Read `${CLAUDE_PLUGIN_ROOT}/skills/build/config.md` first: it defines the config layers and the agent entries.

## What each agent's skills are for

| Agent | Loads its skills when | Good fits |
|---|---|---|
| `orchestrator` | writing the spec and preparing the commit | requirements interviews, spec templates, commit conventions |
| `planner` | breaking the spec into tasks | architecture, API design, planning methods |
| `builder` | building every task and every fix | frameworks, coding style, design and UI, test-driven development |
| `reviewer` | every review | general review checklists |
| `reviewer:<focus>` | only that focus: `correctness`, `security`, `tests`, `ui`, `performance` | security checklists for `security`, accessibility or design review for `ui`, performance guides for `performance` |

## With arguments

Form: `[--global] <agent> add|remove <skill> [<skill>...]`, for example `builder add frontend-design:frontend-design` or `--global reviewer:security add agent-skills:security-and-hardening`.

1. `<agent>` must be one of the entries above. Each skill must appear in your available skills list; refuse any that doesn't and name the closest matches.
2. Target file: `~/.slipyard/config.json` with `--global`, else the project's `.slipyard/config.json`. Create it if needed with only the keys being set. In a project, make sure `.slipyard/.gitignore` exists with the single line `*`.
3. **add**: append to `agents.<agent>.skills` in the target file, skipping duplicates. **remove**: delete from the target file; if the skill comes from the other layer instead, say so and say which command removes it there.
4. Show the result as described in Show.

## Without arguments

1. **Show** the current setup: one row per agent with its skills, each marked `(all projects)` or `(this project)`. Then list the installed skills from your available skills list that fit any agent, grouped by the agent they suit best, one short line each. Leave out Slipyard's own skills.
2. Ask with AskUserQuestion, in one call:
   - which agent to add skills to: `builder`, `reviewer`, `planner`, `orchestrator` (the user can type `reviewer:<focus>` under Other)
   - where: this project, or all projects
3. Ask with AskUserQuestion (multi-select) which skills to add for that agent: up to 4 that fit it best, one line on why each, your recommendation first. The user can type other names under Other.
4. Write them as in With arguments, steps 2 and 3, and show the result.
5. Ask whether to change another agent. Stop when the user says no.

Never change anything except `agents.<agent>.skills` in the chosen file.
