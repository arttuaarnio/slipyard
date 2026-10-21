# How Slipyard works

The details behind the [README](../README.md): every stage, the run folder, the decisions behind the design, and a real run.

## The stages

| # | Stage | Who | What happens |
|---|---|---|---|
| 1 | **Spec** | orchestrator | Reads the code, splits off anything that is really a second feature, and lists its assumptions. A detailed request needs no questions; otherwise it asks only what the request and code can't answer. UI and UX work gets a short design round, using your design skills if you have them. It writes what and why, out of scope, done-when and the verify commands. You approve it and pick the add-on reviewers in one step. |
| 2 | **Plan** | `planner` | Breaks the spec into small slices that each work end to end, riskiest first, each with its test and a done-when check. Small features skip the planner. You approve the task list when there is more than one task. |
| 3 | **Build** | `builder` | One task at a time, each in a fresh context: failing test first, then the code, then the focused tests. It stays in scope and lists anything else it notices instead of fixing it. |
| 4 | **Verify** | orchestrator | Runs the project's own tests, lint, type check and build. A failure goes back to the builder, up to 3 times. |
| 5 | **Review** | `reviewer` × 3-5 | Correctness, security and tests always; UI and performance as add-ons. Findings are checked against the code, blockers and majors go back to the builder, and only the reviewers that found them run again. |
| 6 | **Ship** | you, then orchestrator | One review of everything: the done-when checklist with evidence, the diff, verify results, open findings, leftovers like debug output or missing docs, time and agent tokens per stage, and the proposed commit in your project's style. Approve and commit, request changes, edit the message, or stop. It commits only the files this run changed and never pushes. If a commit hook rejects the commit, it fixes the cause and tries again; it never skips hooks. |

One run is active per repository at a time; starting another asks whether to resume, stop or keep the first.

## Writing a good request

The more your request says, the fewer questions Slipyard asks. A request that names the behaviour, the inputs and outputs, and the edge cases that matter goes straight to a spec you only need to approve:

```
/slipyard:build add a --json flag to `keydrill stats` that prints the same numbers as the table as one JSON object (keys: wpm, accuracy, sessions, per_key), exits 0, and leaves the table output unchanged without the flag
```

A short request like `/slipyard:build add json output` works too, but expect a few questions first.

UI and UX work gets a design round on purpose, because a wrong guess about the look costs a redesign later. Slipyard asks about layout, visual style, the empty, loading and error states, and interaction (screen sizes, keyboard, motion). It skips anything your request, the project's existing design or a design skill already settles. If you have design skills installed but none in the config, it offers the ones that fit and uses your picks for that run. Describe the look in the request to skip most of these questions.

## The run folder

Each run keeps its notes in `.slipyard/runs/<date>-<feature>/`:

| File | Contents |
|---|---|
| `spec.md`, `plan.md` | The approved spec and the task list with progress ticks |
| `verify.md` | The last verify result |
| `diff-<n>.patch`, `review-<n>.md` | What each review round saw and found |
| `noticed.md`, `feedback-<n>.md` | Out-of-scope issues the builders spotted, and your change requests |
| `hook.md` | Output of a commit hook that rejected the commit, if any |
| `summary.md` | What was built, findings left open, time and agent tokens |
| `state.json` | Stage, status, tasks, reviewers, timestamps and token use, so `/slipyard:resume` can continue |

Slipyard writes `.slipyard/.gitignore` containing `*`, so the whole folder, config included, stays out of git without touching your project's own `.gitignore`. Delete that file if you want to commit the config.

## Design decisions

- **A plugin, not an app.** Slipyard is Markdown: four skills and three agents. Claude Code supplies the agent runtime, tools, permissions and UI, so there is nothing to install, build or keep running.
- **Fresh context per task.** Each builder call starts clean with only the spec, the plan and its task. The orchestrator passes file paths, not contents, so long runs stay focused and cheaper.
- **The author doesn't grade its own work.** Reviewers are separate agents with read-only tools, one focus each. The orchestrator checks every blocker and major finding against the code before acting on it, so a wrong finding doesn't turn into a wrong fix.
- **Verification uses the project's own tools.** "Done" means the project's real tests, lint and build pass, not that an agent says it works.
- **Bounded loops.** Verify fixes stop after 3 attempts, review after `maxReviewRounds`, and commit-hook fixes after 2. When that isn't enough, you decide what happens next.
- **Survives long runs.** The orchestrator treats the run folder, not its own memory, as the source of truth, and checks the two agree before every stage. A run still makes sense after Claude Code compacts its context, and `/slipyard:resume` picks it up after a restart.
- **Everything on disk.** Spec, plan, reviews and state live in plain files you can read, diff, resume from, or feed into other tools.
- **Your project, your conventions.** Slipyard detects how a project tests and builds, writes commits in its existing style, and follows its CLAUDE.md. It doesn't ship its own coding style; the README recommends Ponytail for that.

## Example run

A real run in an empty repository, from a deliberately vague request:

```
/slipyard:build build me a react landing page of some sort
```

- **Spec (3 min):** the vague request became a landing page for Slipyard itself, with all copy taken from the README and nothing invented. The spec had 6 sections, 10 done-when checks and verify commands for lint, tests and build. The UI reviewer was added as an add-on.
- **Plan (3 min):** the planner produced 6 tasks, from scaffolding Vite, React and TypeScript with tests to a final layout check at phone and desktop widths. It flagged a trap: the scaffolder offers to delete existing files, which would have wiped `.slipyard/`.
- **Build and verify (14 min):** 6 builder runs, then lint, 11 tests and the production build all passed on the first try.
- **Review round 1:** 4 reviewers found 3 major problems. Copy buttons lost their focus ring to a `clip-path`, the focus ring was invisible on one coloured band, and install commands were cut off at phone width. The builder fixed all three.
- **Review round 2:** only the correctness and UI reviewers ran again, and they confirmed the fixes.
- **Final review:** the user asked for a calmer redesign. The builder reworked it and a full review round found nothing major.
- **Total:** about 640k agent tokens over 30 minutes, 22 of which were the final review.
