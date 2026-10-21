# Evals

Does Slipyard build better features than plain Claude Code, and what does it cost? The same tasks are run both ways and scored on tests neither run has seen.

## Suites

| Suite | Fixture | Requests | Hidden tests check |
|---|---|---|---|
| [`basic`](basic/) | a bookmarks CLI | precise, with every behaviour spelled out | exactly what the request says |
| [`hard`](hard/) | a personal-finance ledger: several modules, `Decimal` money, a planted bug | vague, the way people actually type them | what was asked, plus what a careful engineer handles unasked |

The hard tasks, and what their hidden tests look for beyond the request:

| Task | Request (shortened) | Also checked |
|---|---|---|
| `1-report` | spending per category per month | exact decimal sums, income isn't spending, month and year boundaries, a clean error for a bad month |
| `2-safe-save` | "I lost my ledger when my laptop died while saving" | a real mid-write crash (the process is limited in bytes it may write) must leave the old file intact, and the failure must be reported |
| `3-export` | export a CSV into an exports folder | `../` and absolute names can't escape the folder, and cells can't run as Excel formulas (CSV injection) |
| `4-currencies` | "handle more than one currency" | old ledger files still load, and currencies are never added together |
| `5-dup-import` | "importing the same CSV twice sometimes duplicates" | spacing, `+` signs and Windows line endings, without dropping two genuine identical purchases |

## Method

- **Arms:** each task runs in a fresh copy of the fixture, once as `claude -p "<task>"` (plain) and once as `claude -p "/slipyard:build --auto <task>"` (Slipyard), with the same model, permissions and environment.
- **Scoring:** after a run, the task's `hidden_test.py` is copied in and run through the CLI as a user would. The fixture's original tests are run against the result to catch regressions; the agents' own edits to those tests don't count. Time and cost come from Claude Code's own report.
- **Fairness check:** a reference solution passes every hidden test, and the untouched fixture fails every test of new behaviour. Each hidden test file says what it checks and why.

## Run it

```bash
python3 evals/run.py --suite hard
```

Options: `--tasks 2-safe-save 3-export`, `--arms plain slipyard`, `--model sonnet`, `--parallel 2`. Each run uses your Claude Code login and counts toward your usage. Results go to [`results/`](results/).

Your own Claude Code setup, such as your CLAUDE.md and installed plugins, applies to both arms equally.

## Caveats

- Ten small tasks in two Python projects is a sample, not a benchmark, and each task ran once per arm. Agent runs vary.
- The hard suite's extra checks are judgement calls about what a careful engineer would do. They are written down in each `hidden_test.py`, so you can disagree with them.
