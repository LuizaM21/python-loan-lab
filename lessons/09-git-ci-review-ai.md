# 09 — Git, CI/CD, code review and AI agents

Time: 60 minutes.

Goal: work like a senior on a team: clean Git history, a pipeline that guards main, reviews that
catch real problems, and AI agents you can trust.

## Learn: Git that interviewers ask about

| Task | Command |
| --- | --- |
| Feature branch | `git switch -c feat/repayments-list` |
| Small commits, clear messages | `feat: list repayments of a loan`, `fix: reject overpayment by one cent` (Conventional Commits) |
| Update your branch | `git fetch && git rebase origin/main` (linear history) or `git merge origin/main` |
| Clean up before review | `git rebase -i origin/main` (squash "fix typo" commits) |
| Resolve a conflict | edit, `git add`, `git rebase --continue` |
| Find the commit that broke it | `git bisect start`, `git bisect bad`, `git bisect good <sha>`, `git bisect run pytest -x` |
| Undo safely on a shared branch | `git revert <sha>` (never rewrite pushed history) |
| See who changed a line and why | `git log -p -L 80,95:loanlab/services.py`, `git blame` |

Rebase vs merge: rebase rewrites **your** unpublished commits for a straight history; merge keeps
history as it happened. Never rebase a branch others already use.

## Learn: the pipeline

`.github/workflows/ci.yml` runs on every push and pull request:

| Job | Runs | Fails when |
| --- | --- | --- |
| lint | `ruff check`, `ruff format --check`, `mypy` | style or type errors |
| test | `pytest --cov` (+ Django tests) | a test fails |
| perf-smoke | starts the API, `k6 run perf/smoke.js` | p95 or error-rate threshold |
| docker | `docker build` | the image does not build |

What runs when: on every PR, the fast checks (minutes). On merge to main: build and push the
image, deploy to a test environment. Nightly: longer load tests, dependency and image scans.
`ci/gitlab-ci.example.yml` shows the same in GitLab.

## Learn: reviewing code

Review in this order: **correctness** (does it do what the ticket says, edge cases, errors) ->
**safety** (money, security, data, transactions) -> **tests** (do they prove the behaviour?) ->
**design** (right layer, simple) -> **style** (let the linter do it). Be specific and kind: say
what, why, and a suggestion. Separate "must fix" from "nit".

## Learn: AI agents (Claude Code) for developers

Useful for: reading unfamiliar code, writing the boring parts of tests, refactoring with tests
green, explaining a stack trace, drafting a migration, reviewing a diff against a checklist.

How to trust the output: **context** (`CLAUDE.md` has the rules and commands), **small tasks**,
**tests as the oracle** (the agent must run them; see a new test fail once), **review every
line** like a colleague's PR, never paste secrets or real customer data. You stay accountable
for what you merge.

This repo has `CLAUDE.md`, two skills (`.claude/skills/implement-feature`,
`.claude/skills/triage-test-failure`) and a reviewer agent (`.claude/agents/code-reviewer.md`).

## In this repo

| File | Shows |
| --- | --- |
| `.github/workflows/ci.yml` | the pipeline |
| `ci/gitlab-ci.example.yml` | the same in GitLab |
| `lessons/assets/review-me.diff` | a pull request to review |
| `CLAUDE.md`, `.claude/` | context, skills and an agent for Claude Code |

## Do

### 1. Branches and PRs

Do your lesson 03 and 04 features on branches, open pull requests on GitHub, and merge them.
Watch the pipeline run. Make it fail once on purpose (a failing assertion), read the log, fix it.

### 2. Bisect

Turn on a bug and commit it (`instructor/bug.sh random 1`, `git commit -am "wip"`), add three
harmless commits, then find the bad commit with `git bisect run pytest -x` (your tests must
catch it). Afterwards: `git bisect reset`, `git reset --hard <sha-before-the-experiment>`, then
`instructor/bug.sh reset` to clear the bug list.

### 3. Review a pull request

Read `lessons/assets/review-me.diff` as if a colleague asked for your review. Write your review in
`notes/review-42.md`: every problem, why it matters, the fix, and "must fix" or "nit". There are
at least 10 real problems. Then say what tests you would ask for.

### 4. CI improvements

Add to the pipeline: a coverage report kept as an artifact; fail the build if coverage of
`loanlab/` drops below 85%. Run the katas only on a schedule (nightly), not on every push.

### 5. An AI-assisted feature

With Claude Code (or another agent), using the `implement-feature` skill: "Add `GET
/api/customers/<name>/loans`". Review its diff with the `code-reviewer` agent and then yourself.
Write in `notes/day-5.md` one thing it did well and one thing you had to correct.

## Check yourself

1. Rebase vs merge: when each? What must you never rebase?
2. How does `git bisect run` work?
3. What runs on a PR, on merge, and nightly? Why split them?
4. What do you look at first in a review, and what do you leave to tools?
5. Name five problems in PR #42.
6. How do you make AI-written code trustworthy?

## Say it in the interview

- "I keep PRs small, with tests, and a description that says why. I review for correctness and
  safety first, style last: the linter does style."
- "The pipeline guards main: lint, types, tests with coverage, a performance smoke test and an
  image build on every PR."
- "I use AI agents for speed, with tests as the oracle and a human review of every line."
