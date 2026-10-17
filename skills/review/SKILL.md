---
name: review
description: Review the current uncommitted changes, or everything since a given git ref, with Slipyard reviewer subagents in parallel - correctness, security and tests, plus ui and performance if chosen - and report merged findings. Read-only; changes no code.
argument-hint: "[--model <model>] [--effort <level>] [base-ref]"
---

# Slipyard: review changes

Run only Slipyard's review stage, on changes made outside a `/slipyard:build` run. Report findings; don't change any code unless the user asks afterwards.

Arguments: $ARGUMENTS

1. **Parse the arguments.** `--model` and `--effort` override the reviewer's model and effort for this review. A remaining argument is the base ref to diff against; default `HEAD`, which means the uncommitted changes.
2. **Check the repository.** It must be a git repository with at least one commit. Read `.slipyard/config.json` if it exists; without it, use `${CLAUDE_PLUGIN_ROOT}/config.default.json`. Model and effort come from the overrides, else `agents.reviewer`.
3. **Write the change set.** Create `.slipyard/reviews/` if needed, and `.slipyard/.gitignore` with the lines `runs/` and `reviews/` if it doesn't exist. Write `.slipyard/reviews/<YYYYMMDD-HHMM>.patch` (local time, from `date +%Y%m%d-%H%M`): `git diff <base> -- . ':!.slipyard'`, then the untracked files (`git ls-files --others --exclude-standard`, skipping `.slipyard/`) as a list at the end. If there is nothing to review, say so and stop.
4. **Pick the reviewers.** `correctness`, `security` and `tests` always run. Ask with AskUserQuestion (multi-select) which add-ons to run too: `ui` (accessibility, states and layout of a user-facing interface) and `performance` (how cost grows with input, hot paths, unbounded memory). Recommend `ui` when the patch changes a user-facing interface and `performance` when it touches hot paths, large data or queries; also recommend anything in `addonReviewers`.
5. **Run them.** Call one `slipyard:reviewer` per focus, in parallel: foreground calls (`run_in_background: false`) in one message. Give each its focus and the patch path, and say there is no spec, so it judges the change by what it appears to intend. If `skills.review` lists skills you can see in your available skills list, end each prompt with: "Before you start, load these skills with the Skill tool and apply them where they don't conflict with your instructions: <names>." Mention any listed skill you can't find.
6. **Merge.** Write `.slipyard/reviews/<YYYYMMDD-HHMM>.md`: drop duplicates, keep file:line, severity and focus, group by severity. Check each `blocker` and `major` against the code yourself; drop the ones that are wrong and say why.
7. **Report.** Show the findings, most severe first, and the path of the saved file.
