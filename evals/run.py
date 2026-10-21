#!/usr/bin/env python3
"""Run each eval task with plain Claude Code and with Slipyard, then score both
against hidden acceptance tests that neither run sees.

    python3 evals/run.py --suite basic          # all tasks, both arms
    python3 evals/run.py --suite hard --tasks 2-safe-save --arms slipyard

Needs the `claude` CLI, logged in. Each run works in a fresh temp copy of the
suite's fixture; nothing in this repo is changed. Results go to evals/results/.
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

EVALS = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(EVALS)
TOOLS = "Bash Read Write Edit Grep Glob Agent Skill"


def sh(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)


def make_repo(suite):
    work = tempfile.mkdtemp(prefix="slipyard-eval-")
    repo = os.path.join(work, "repo")
    shutil.copytree(os.path.join(EVALS, suite, "fixture"), repo)
    for cmd in (["git", "init", "-q", "-b", "main"],
                ["git", "add", "-A"],
                ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.com",
                 "commit", "-qm", "Initial"]):
        sh(cmd, repo, check=True)
    sh(["git", "config", "user.name", "eval"], repo)
    sh(["git", "config", "user.email", "eval@example.com"], repo)
    return repo


def unittest_counts(output):
    """(passed, total) from unittest output."""
    ran = re.search(r"Ran (\d+) tests?", output)
    total = int(ran.group(1)) if ran else 0
    bad = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", output))
    return total - bad, total


def score(repo, suite, task):
    """Hidden tests passed, existing tests still passing, and diff size."""
    tests = os.path.join(repo, "tests")
    shutil.copy(os.path.join(EVALS, suite, "tasks", "helpers.py"), os.path.join(tests, "helpers.py"))
    shutil.copy(os.path.join(EVALS, suite, "tasks", task, "hidden_test.py"), os.path.join(tests, "test_hidden.py"))
    hidden = sh([sys.executable, "-m", "unittest", "tests.test_hidden"], repo, timeout=300)
    # Regressions: the fixture's original tests, not the agent's edited copies.
    # A task may list the original tests that stay valid in its existing_tests.txt.
    copied = ["helpers.py", "test_hidden.py"]
    for name in os.listdir(os.path.join(EVALS, suite, "fixture", "tests")):
        if name.startswith("test_"):
            shutil.copy(os.path.join(EVALS, suite, "fixture", "tests", name), os.path.join(tests, "orig_" + name))
            copied.append("orig_" + name)
    override = os.path.join(EVALS, suite, "tasks", task, "existing_tests.txt")
    if os.path.exists(override):
        with open(override, encoding="utf-8") as f:
            ids = ["tests.orig_" + line for line in f.read().split()]
    else:
        ids = ["tests." + name[:-3] for name in copied if name.startswith("orig_")]
    existing = sh([sys.executable, "-m", "unittest", *ids], repo, timeout=300)
    for name in copied:
        os.remove(os.path.join(tests, name))
    sh(["git", "add", "-A", "--", ".", ":!.slipyard"], repo)
    base = sh(["git", "rev-list", "--max-parents=0", "HEAD"], repo).stdout.strip()
    stat = sh(["git", "diff", "--cached", "--shortstat", base], repo).stdout
    lines = sum(int(n) for n in re.findall(r"(\d+) (?:insertion|deletion)", stat))
    return {
        "hidden": unittest_counts(hidden.stderr),
        "existing_ok": existing.returncode == 0,
        "lines_changed": lines,
    }


def run_one(suite, task, arm, model, timeout):
    repo = make_repo(suite)
    with open(os.path.join(EVALS, suite, "tasks", task, "task.md"), encoding="utf-8") as f:
        prompt = f.read().strip()
    cmd = ["claude", "-p", "--model", model, "--permission-mode", "acceptEdits",
           "--allowedTools", TOOLS, "--output-format", "json"]
    if arm == "slipyard":
        cmd += ["--plugin-dir", PLUGIN]
        prompt = "/slipyard:build --auto " + prompt
    # A clean environment, so a parent Claude Code session doesn't leak into the run.
    env = {k: os.environ[k] for k in ("HOME", "PATH", "USER", "LANG") if k in os.environ}
    started = datetime.datetime.now()
    try:
        proc = subprocess.run(cmd + [prompt], cwd=repo, env=env, capture_output=True,
                              text=True, timeout=timeout)
        result = json.loads(proc.stdout or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        result = {"is_error": True, "result": f"{type(e).__name__}"}
    seconds = (datetime.datetime.now() - started).total_seconds()
    return {
        "suite": suite, "task": task, "arm": arm, "model": model, "repo": repo,
        "seconds": round(seconds), "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"), "error": result.get("is_error", False),
        "reply": (result.get("result") or "")[:500],
        **score(repo, suite, task),
    }


def table(rows):
    lines = ["| Task | Arm | Hidden tests | Existing tests | Lines | Time | Cost |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        passed, total = r["hidden"]
        cost = f"${r['cost_usd']:.2f}" if r["cost_usd"] is not None else "?"
        lines.append(f"| {r['task']} | {r['arm']} | {passed}/{total} | "
                     f"{'pass' if r['existing_ok'] else 'FAIL'} | {r['lines_changed']} | "
                     f"{r['seconds']} s | {cost} |")
    for arm in sorted({r["arm"] for r in rows}):
        mine = [r for r in rows if r["arm"] == arm]
        passed = sum(r["hidden"][0] for r in mine)
        total = sum(r["hidden"][1] for r in mine)
        cost = sum(r["cost_usd"] or 0 for r in mine)
        secs = sum(r["seconds"] for r in mine)
        lines.append(f"| **all** | **{arm}** | **{passed}/{total}** | "
                     f"{sum(r['existing_ok'] for r in mine)}/{len(mine)} pass | | "
                     f"{secs // 60} min | ${cost:.2f} |")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suite", default="basic", choices=["basic", "hard"])
    p.add_argument("--tasks", nargs="+", help="task folder names; default all in the suite")
    p.add_argument("--arms", nargs="+", default=["plain", "slipyard"], choices=["plain", "slipyard"])
    p.add_argument("--model", default="sonnet")
    p.add_argument("--parallel", type=int, default=2, help="runs at the same time")
    p.add_argument("--timeout", type=int, default=1800, help="seconds per run")
    args = p.parse_args()
    tasks_dir = os.path.join(EVALS, args.suite, "tasks")
    all_tasks = sorted(d for d in os.listdir(tasks_dir) if os.path.isdir(os.path.join(tasks_dir, d)))
    args.tasks = args.tasks or all_tasks
    unknown = set(args.tasks) - set(all_tasks)
    if unknown:
        p.error(f"unknown tasks: {', '.join(sorted(unknown))}")

    jobs = [(t, a) for t in args.tasks for a in args.arms]
    with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
        futures = [pool.submit(run_one, args.suite, t, a, args.model, args.timeout) for t, a in jobs]
        rows = []
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"{row['task']:10} {row['arm']:9} hidden {row['hidden'][0]}/{row['hidden'][1]}"
                  f"  {row['seconds']} s  ${row['cost_usd'] or 0:.2f}", flush=True)
    rows.sort(key=lambda r: (r["task"], r["arm"]))

    os.makedirs(os.path.join(EVALS, "results"), exist_ok=True)
    stamp = args.suite + "-" + datetime.datetime.now().strftime("%Y%m%d-%H%M")
    with open(os.path.join(EVALS, "results", f"{stamp}.json"), "w", encoding="utf-8") as f:
        # Scores only: agent replies and temp paths can carry details of the local setup.
        json.dump([{k: v for k, v in r.items() if k not in ("reply", "repo")} for r in rows], f, indent=2)
    report = table(rows)
    with open(os.path.join(EVALS, "results", f"{stamp}.md"), "w", encoding="utf-8") as f:
        f.write(f"# Eval run {stamp}\n\nModel: {args.model}\n\n{report}\n")
    print("\n" + report)


if __name__ == "__main__":
    main()
