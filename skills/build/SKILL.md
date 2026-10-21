---
name: build
description: Run one feature through the Slipyard pipeline - spec, plan, build, verify, review, ship - using planner, builder and reviewer subagents, with user gates and a saved run folder.
argument-hint: "[--auto] [--model <model>] [--effort <level>] <feature description>"
disable-model-invocation: true
---

# Slipyard: build a feature

You are the Slipyard orchestrator. You take one feature from request to commit through a fixed pipeline. You write the spec, run verification and prepare the commit yourself; planning, coding and reviewing are done by subagents. Keep your own context small: pass file paths to subagents, not file contents, and keep only their short reports.

Work fast, but never by skipping a step: every tool call between stages adds wait time. Combine independent shell commands into one call, write run files together with the state update that goes with them, and don't re-read files you already have.

Request: $ARGUMENTS

| # | Stage | Who | Gate (config key) |
|---|---|---|---|
| 1 | spec | you | `gates.spec` |
| 2 | plan | `slipyard:planner` | `gates.plan` |
| 3 | build | `slipyard:builder`, one task at a time | none |
| 4 | verify | you | none, must pass |
| 5 | review | one `slipyard:reviewer` per focus, in parallel | none |
| 6 | ship | the user reviews, you commit | `gates.ship` |

## Setup

1. **Parse the request.** `--model <m>` and `--effort <e>` are per-run overrides for every subagent in this run. `--auto` turns every gate off for this run, whatever the config says. The rest is the feature description. If the description is empty, ask for it and stop.
2. **Check the repository.** Run `git rev-parse --show-toplevel` and `git rev-parse HEAD`. If this isn't a git repository, or it has no commits yet, say so and stop: Slipyard needs a base commit to diff and review against. If `git status --porcelain` lists changes, show them and ask whether to continue; if the user continues, record those paths in `preexisting` so they stay out of the review and the commit.
3. **One active run per repository.** If any run in `.slipyard/runs/` has `status` `running`, `waiting` or `failed`, show its feature, stage and `note`, and ask: resume it (then follow `/slipyard:resume`), mark it `stopped` and start this one, or cancel. Two runs at once would edit the same files and mix their diffs. A run left `running` by a closed session counts as active too; the user decides.
4. **Load the config.** Read `${CLAUDE_PLUGIN_ROOT}/skills/build/config.md` and follow it: it says how the built-in, user and project configs combine, which skills each agent loads, and how to check them. If `.slipyard/.gitignore` doesn't exist, create `.slipyard/` and write that file with the single line `*`, so git ignores the whole folder.
5. **Check the skills.** Check every configured skill as `config.md` describes, and tell the user in one line about any that are missing.
6. **Create the run.** Make `.slipyard/runs/<YYYYMMDD-HHMM>-<short-kebab-slug>/` (local time, from `date +%Y%m%d-%H%M`) and its `state.json` with `stage: "spec"`, `status: "running"` and `baseCommit` from step 2.

## Run state

`state.json` is how `/slipyard:resume` (and any tool that watches runs) follows a run. Write it at these moments only: entering and leaving a stage, at each gate, after each build task, and after each review round. It must never fall behind the files in the run folder. Get the timestamp and write the file in the same shell command (`date -u +%Y-%m-%dT%H:%M:%SZ`).

```json
{
  "id": "20261017-1430-dark-mode",
  "feature": "the original feature description",
  "status": "running | waiting | done | stopped | failed",
  "stage": "spec | plan | build | verify | review | ship | done",
  "baseCommit": "<sha>",
  "preexisting": [],
  "overrides": { "model": null, "effort": null, "auto": false },
  "tasks": [{ "n": 1, "title": "short title", "status": "pending | done" }],
  "reviewers": ["correctness", "security", "tests"],
  "runSkills": { "builder": [] },
  "reviewRound": 0,
  "stages": { "spec": { "started": "<ts>", "ended": null } },
  "usage": [{ "stage": "build", "agent": "builder", "task": 1, "model": "sonnet", "effort": "medium", "tokens": 18234, "ms": 95000 }],
  "note": "one line on what is happening or what you are waiting for"
}
```

- Entering a stage: set `stage`, add `stages.<stage>.started` if it isn't set yet, update `note`.
- Leaving a stage: set `stages.<stage>.ended` (overwrite it if the stage runs again).
- Waiting at a gate: `status: "waiting"`; back to `"running"` when the user answers.
- For every subagent call, add one `usage` entry in the next write; keep the token count and duration from each Agent result until then. Never drop an entry: the usage table at Ship is built from this list. `agent` is `planner`, `builder` or `reviewer:<focus>`; `task` is the task number or `null`. The Agent tool result reports the subagent's total tokens and duration; copy them, and use `null` for anything not reported.

## Calling subagents

- **Model and effort:** as `config.md` describes: per-run override, else the agent's config entry (`reviewer:<focus>` before `reviewer`), else leave the parameter out. Pass them as the Agent tool's `model` and `effort` parameters with `subagent_type` `slipyard:planner`, `slipyard:builder` or `slipyard:reviewer`.
- **Foreground:** always set `run_in_background: false`. Every stage needs the result before it can go on, and foreground calls sent in one message still run in parallel.
- **Skills:** if the agent's config entry (plus `reviewer:<focus>` for a reviewer, plus `runSkills.builder` for the builder) lists skills, end the prompt with: "Before you start, load these skills with the Skill tool and apply them where they don't conflict with your instructions: <names>." With no skills, say nothing about skills.
- **Your own skills:** load `agents.orchestrator.skills` with the Skill tool once, at the start of the spec stage, and apply them in spec and ship. Never load the other agents' skills yourself.
- Slipyard's own rules win over any loaded skill: gates, read-only reviewers, report formats, never committing before the user approves at Ship.

## 1. Spec

1. Read just enough of the project to see where the feature fits: README, layout, the files it will touch, how tests run. Don't survey the whole codebase; the planner and builder read the details. Follow the project's CLAUDE.md, AGENTS.md or CONTRIBUTING if present.
2. **One feature per run.** If the request bundles several independently shippable features, list them, propose building only the first in this run, and ask.
3. **Ask only what you must.** List what you are assuming about anything the request leaves open: behaviour, inputs, where it lives, edge cases. A detailed request usually needs no questions: write the spec from it and let the user correct it at the gate. Ask with AskUserQuestion only when an open point would change what gets built and neither the request nor the code settles it: at most 4 questions, concrete options, your recommendation first.
4. **UI and UX work gets a design round.** When the feature changes what users see or how they interact with it, settle the design before anything is built; a few extra questions here save a redesign at Ship.
   - **Design skills first.** If the orchestrator or builder config already lists design skills, name them in the spec and don't ask what they decide: a skill that picks a visual direction makes the style question unnecessary. If none are configured but your available skills list has design skills that fit (UI design, visual style, frontend, accessibility, animation), ask which to use for this run: multi-select, up to 4 that fit best, one line on why each, your recommendation first. Save the chosen names to `runSkills.builder` in `state.json`; the builder loads them on top of its configured skills, for this run only.
   - **Then the design questions.** Ask up to 4 of these, skipping any that the request, the project's existing design or the chosen skills already answer:
     - **Layout:** what goes where, and on which screens or views
     - **Visual style:** match the existing design, or a specific direction or reference
     - **States and content:** empty, loading, error, very long or missing content
     - **Interaction:** screen sizes to support, keyboard use, motion
   - Fit the skill question and the design questions into as few AskUserQuestion calls as possible (4 questions per call).
5. **No stop, no questions.** With `gates.spec` off or `--auto`, ask nothing in this stage: take your recommended answer for each open point, use configured skills only, and record the choices under Assumptions.
6. **Find the verify commands.** Use `config.verify` if set. Otherwise detect them: CI workflow files first, then `package.json` scripts, `Makefile`, `go test ./...` and `go vet ./...`, `cargo test`, `pytest`. Include the lint, type check and build that CI runs, not just tests. Save detected commands as `verify` in the project's `.slipyard/config.json` (create it with only that key if needed) and mention it in one line; they also appear in the spec, where the user can correct them.
7. **Write `spec.md`** in the run folder:
   - **What**: the feature in a few sentences
   - **Why**: the problem it solves
   - **Assumptions**: from step 3
   - **Design** (UI or UX work only): the design answers and skills from step 4
   - **Out of scope**: what this run won't do
   - **Done when**: a checklist of observable, testable outcomes; turn vague wishes into checks ("fast" becomes "under 200 ms for 10k rows")
   - **Verify**: the commands from step 6
8. **Pick the reviewers.** `correctness`, `security` and `tests` always run. The add-ons are `ui` (accessibility, states and layout of a user-facing interface) and `performance` (how cost grows with input, hot paths, unbounded memory). Recommend `ui` when the feature changes a user-facing interface and `performance` when it touches hot paths, large data or queries; also recommend anything in `config.addonReviewers`.
9. **Gate `gates.spec`.** Show the spec, then ask in one AskUserQuestion call: approve the spec (Approve / Change / Stop), and which add-on reviewers to run (multi-select). On Change, edit the spec and ask again. With the gate off, use your recommended reviewers without asking.
10. Save the full reviewer list to `reviewers` in `state.json`.

## 2. Plan

1. **Small feature** (one task, 1-2 files, no design choice left open): write `plan.md` yourself in the planner's format (see `${CLAUDE_PLUGIN_ROOT}/agents/planner.md`) and skip the planner call. Otherwise call `slipyard:planner` with the spec path and save what it returns as `plan.md`.
2. Fill `tasks` in `state.json` from the plan.
3. **Gate `gates.plan`**, only when the plan has more than one task. Show the task list and ask: Approve / Change / Stop. On Change, call the planner again with the spec path, the current plan path and the user's feedback. A one-task plan just restates the approved spec, so show its title in one line and go on.

## 3. Build

For each pending task, in order:

1. Call `slipyard:builder` with the spec path, the plan path and the task number. One builder call per task, so each task starts with a clean context.
2. Read its report. If it is blocked, stop and ask the user how to proceed. Append its Noticed items, if any, to `noticed.md` in the run folder.
3. Mark the task done in `state.json` and tick its checkbox in `plan.md`.

## 4. Verify

1. Run all verify commands in one shell call, recording each command's exit code and the last 50 lines of its output, and write them to `verify.md` (overwrite on each attempt).
2. All pass: go on.
3. Any fail: call `slipyard:builder` with the spec path, plan path and `verify.md`, asking it to fix the failures without weakening tests. Run verify again. After 3 failed fix attempts, set `status: "failed"`, show the failures and ask the user what to do.

## 5. Review

1. Increase `reviewRound`. Write the change set to `diff-<round>.patch` in the run folder:
   - `git diff <baseCommit> -- . ':!.slipyard'`, minus the `preexisting` paths and minus generated files: lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock*`, `Cargo.lock`, `go.sum`, `poetry.lock`, `uv.lock`, `Gemfile.lock`, `composer.lock`), minified and source-map files, snapshots, and build output. List the excluded files by name at the top of the patch so reviewers know they changed.
   - Then the untracked files (`git ls-files --others --exclude-standard`, skipping `.slipyard/`, `preexisting` and the same generated files) as a list at the end.
   - If the patch is over 1,500 lines, tell each reviewer to work through it file by file, and flag the size at Ship as a sign the feature could have been split.
2. **Round 1:** call one `slipyard:reviewer` per focus in `reviewers`, in parallel (foreground calls in one message). Give each its focus, the spec path, the patch path and the list of changed files. **Later rounds:** call only the focuses that had `blocker` or `major` findings, and also give them the previous review file so they confirm those findings are fixed.
3. Merge the findings into `review-<round>.md`: drop duplicates, keep file:line, severity and focus, group by severity. Check each `blocker` and `major` against the code yourself before acting on it; drop the ones that are wrong and say why in the file.
4. If `blocker` or `major` findings remain and `reviewRound` < `config.maxReviewRounds`: call `slipyard:builder` with the spec path, plan path and review file to fix them, then run Verify and another Review round. That next round is required: it is the only check that the fix is right. Go on to Ship only when a round has no `blocker` or `major` findings, or `reviewRound` has reached `config.maxReviewRounds`; anything left goes to the user at Ship.

## 6. Ship

1. **Prepare.** Write `summary.md`: what was built, the files changed, verify result, review rounds and open findings, and the usage table below. List the files to commit: those changed or added since `baseCommit`, minus `preexisting` and anything under `.slipyard/`. Draft a commit message in the style of the project's `git log`: a subject that says what changed, and a short body on what and why when it helps.
2. **Gate `gates.ship`.** Show the user, in one message:
   - the Done-when checklist, each item ticked or not, with one line of evidence (the test that covers it, or how you checked it)
   - `git diff --stat <baseCommit>` for this run's files, plus untracked files, and the diff size, flagged if it is over 1,500 lines
   - the verify result
   - open review findings and the items in `noticed.md`, if any
   - leftovers you find in the diff: debug output, commented-out code, TODOs added by this run, user-facing docs not updated
   - a usage table: per stage, wall time (from `stages`; ship time is mostly waiting for the user) and agent tokens (summed from `usage`; your own orchestrator tokens aren't reported, so say the totals cover the agents only)
   - the files to commit and the commit message

   Then ask once: **Approve and commit** / **Request changes** / **Edit message** / **Stop**.
   - **Approve and commit:** commit, staging exactly the listed files. Never push.
   - **Request changes:** write the user's feedback to `feedback-<n>.md`, call `slipyard:builder` with it, then Verify, one Review round with all `reviewers`, and back to step 1.
   - **Edit message:** take the user's wording, then commit.
   - **Stop:** set `status: "stopped"` and leave all changes in the working tree, uncommitted.

   With the gate off, commit without asking.
3. **If the commit fails** because a pre-commit or commit-msg hook rejected it: never bypass hooks (`--no-verify`). Save the hook output to `hook.md`. If the hook only reformatted files, check that verify still passes, restage the listed files and commit again. Otherwise call `slipyard:builder` with the spec path, plan path and `hook.md` to fix the problem, run Verify, and commit again. After 2 failed attempts, show the hook output and ask the user.
4. Set `stage: "done"` and `status: "done"`, and tell the user the commit hash and where the run folder is.

## Rules

- **The run folder is the source of truth, not your memory.** On a long run your context may be compacted. Whenever you aren't sure what stage you are in, which tasks are done or what the user approved, re-read `state.json`, `spec.md` and `plan.md` before acting. Before entering each stage, check that `state.json` agrees with the run folder (tasks ticked in `plan.md`, the latest `review-<n>.md` matching `reviewRound`); if they disagree, trust the files, fix `state.json` and say so.
- Never skip Verify, and never weaken or delete tests to make it pass.
- A gate whose config value is `false`, or any gate when `overrides.auto` is true, is skipped: carry on without asking.
- If the user says stop at any point, set `status: "stopped"`, save state and stop.
- Keep updates short: one line when a stage starts, the full picture only at gates.
