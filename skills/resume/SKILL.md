---
name: resume
description: Resume a stopped or interrupted Slipyard run from its saved state in .slipyard/runs/.
argument-hint: "[run-id]"
disable-model-invocation: true
---

# Slipyard: resume a run

Arguments: $ARGUMENTS

1. **Pick the run.** The folder `.slipyard/runs/<run-id>/` if a run id was given, else the newest run whose `state.json` `status` isn't `done`. If there is none, list the five most recent runs with their feature and status, and stop.
2. **Load the pipeline.** Read `${CLAUDE_PLUGIN_ROOT}/skills/build/SKILL.md` and follow it from here on. Redo its Setup steps 4 and 5 (config and skills), but don't create a new run.
3. **Load the run.** Read `state.json` and the files in the run folder: `spec.md`, `plan.md`, `noticed.md`, the latest `verify.md`, `review-<n>.md` and `feedback-<n>.md`. Use `overrides` from `state.json` as the run's `--model` and `--effort`, and its `reviewers` (`correctness`, `security`, `tests` if missing) and `preexisting` (empty if missing).
4. **Check the working tree.** Run `git status` and `git diff --stat <baseCommit>`. If `baseCommit` is no longer an ancestor of `HEAD`, or the tree looks different from what the run expects, say what changed and ask before going on.
5. **Report.** Tell the user in two or three lines where the run stands: feature, stage, tasks done, last note.
6. **Continue** at the recorded `stage`, with `status` back to `"running"`. Within build, continue at the first pending task. A run that stopped at a gate shows that gate again.
