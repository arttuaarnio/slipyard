# Slipyard config

How every Slipyard skill reads its settings.

## Layers

Read these in order; each one overrides the one before:

1. `${CLAUDE_PLUGIN_ROOT}/config.default.json`: the built-in defaults
2. `~/.slipyard/config.json`: the user's settings for every project, if it exists (check; if it doesn't, there are no global settings)
3. `.slipyard/config.json` in the project, if it exists

Merge objects key by key, so a layer only needs the keys it changes. A value that isn't an object replaces the earlier one, except `skills` lists: those add up across layers, so skills set for every project and skills set for this project both load. If a file isn't valid JSON, show the file path and the error, and stop.

Never copy the defaults into a project or user config: a full copy would hide later changes in the other layers. Write only the keys being set.

## Agents

`agents` has one entry per agent:

| Entry | Keys | Used by |
|---|---|---|
| `orchestrator` | `skills` | you, in the spec and ship stages |
| `planner` | `model`, `effort`, `skills` | `slipyard:planner` |
| `builder` | `model`, `effort`, `skills` | `slipyard:builder`, for tasks and for every fix (verify, review findings, commit hooks, user feedback) |
| `reviewer` | `model`, `effort`, `skills` | every `slipyard:reviewer` |
| `reviewer:<focus>` | `model`, `effort`, `skills` | only the reviewer with that focus: `correctness`, `security`, `tests`, `ui` or `performance` |

A `reviewer:<focus>` entry overrides `reviewer`'s model and effort for that focus, and its skills are added to `reviewer`'s.

Model and effort for a call: the run's `--model` and `--effort`, else the agent's entry, else leave the parameter out.

## Skills

A skill name is written as Claude Code shows it: `plugin:skill` for plugin skills, the plain name for the user's own. Before using any, check each configured name against your available skills list. Tell the user in one line about any you can't find, and leave it out.

## Older configs

- A top-level `skills` object maps to the agents: `spec` and `ship` to `orchestrator`, `plan` to `planner`, `build` to `builder`, `review` to `reviewer`.
- `gates.humanReview` means `gates.ship` is on if either of them is true.
