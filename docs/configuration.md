# Configuring Slipyard

Slipyard works with no configuration. This page is for when you want it to work your way.

## Skills

Slipyard works without any setup. Its agents already follow a strong engineering baseline: an agreed spec, small tasks, test-first building, independent reviews and the project's own checks. Skills are how you add your own way of working on top: a design system for the builder, a security checklist for the security reviewer, your team's spec template for the orchestrator.

Add as many or as few as you like, to any agent:

```
/slipyard:skills builder add frontend-design:frontend-design
/slipyard:skills reviewer:security add agent-skills:security-and-hardening
/slipyard:skills --global orchestrator add agent-skills:interview-me
/slipyard:skills
```

The last form, with no arguments, shows what each agent loads now and suggests skills you have installed that fit each one. `--global` sets a skill for all your projects.

| Agent | Loads its skills when | Good fits |
|---|---|---|
| `orchestrator` | writing the spec and preparing the commit | requirements interviews, spec templates, commit conventions |
| `planner` | breaking the spec into tasks | architecture, API design |
| `builder` | building every task and every fix | frameworks, coding style, design and UI, test-driven development |
| `reviewer` | every review | general review checklists |
| `reviewer:<focus>` | only that reviewer: `correctness`, `security`, `tests`, `ui`, `performance` | a security checklist for `security`, accessibility or design review for `ui` |

Skills add to Slipyard's rules and never override them: reviewers stay read-only, and nothing is committed before you approve at Ship. A configured skill that isn't installed is reported at the start of a run and skipped. For UI and UX features, design skills you have installed but haven't configured are offered at the spec stop and used for that run only.

## Settings

Settings come in three layers, each overriding the one before:

1. Slipyard's built-in defaults
2. `~/.slipyard/config.json`: yours, for every project
3. `.slipyard/config.json`: this project only

A layer only needs the keys it changes. Skill lists add up across layers, so your global skills and a project's skills both load. The built-in defaults:

```json
{
  "gates": { "spec": true, "plan": true, "ship": true },
  "maxReviewRounds": 2,
  "addonReviewers": [],
  "agents": {
    "orchestrator": { "skills": [] },
    "planner": { "model": "opus", "effort": "high", "skills": [] },
    "builder": { "model": "sonnet", "effort": "medium", "skills": [] },
    "reviewer": { "model": "sonnet", "effort": "high", "skills": [] }
  },
  "verify": []
}
```

| Key | Meaning |
|---|---|
| `gates` | Which stops ask you: `spec`, `plan` (only for plans with more than one task) and `ship` (your review and the commit). Set one to `false` to skip it; all three `false`, or `--auto` for one run, goes start to finish unattended. |
| `maxReviewRounds` | How many review-and-fix rounds run before leftover findings go to you. |
| `addonReviewers` | Add-on reviewers to recommend at the spec stop: `"ui"`, `"performance"`. You still choose each run. With the spec gate off, these run without asking. |
| `agents` | Per agent: `model` (`opus`, `sonnet`, `haiku`, or a full model ID), `effort` (`low` to `max`) and `skills`. Add a `reviewer:<focus>` entry, such as `"reviewer:security": { "model": "opus" }`, to give one reviewer its own model, effort or skills. |
| `verify` | Commands that must pass, such as `["npm run lint", "npm test", "npm run build"]`. Left empty, Slipyard detects them from CI and build files and saves them to the project config. |

## Fewer permission prompts

The builder edits files and runs your test commands, and in Claude Code's default mode each of those asks for approval. For runs that only stop at Slipyard's own gates:

- Start Claude Code in accept-edits mode, so file edits are approved automatically:

  ```bash
  claude --permission-mode acceptEdits
  ```

- Allow your project's verify commands in `.claude/settings.json` (shared) or `.claude/settings.local.json` (just you):

  ```json
  {
    "permissions": {
      "allow": ["Bash(npm run *)", "Bash(npx vitest *)"]
    }
  }
  ```

Reviewers are read-only and never prompt. Slipyard's gates still stop for you, and it never pushes.
