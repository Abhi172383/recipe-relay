# Planned Merge-Conflict Exercise — RecipeRelay

## Objective
Demonstrate team Git conflict detection, inspection, manual resolution, and verification using feature branches.

## Setup & Conflicting Commits
1. Created branch `docs/merge-conflict-exercise` from `main` and updated line 12 of `docs/qa-checklist.md` (commit `44b209f`) to record the measured `94%` backend statement coverage.
2. Switched to `main` and edited the same line of `docs/qa-checklist.md` (commit `4a356b7`) to document CI `coverage.xml` enforcement.
3. Merged `docs/merge-conflict-exercise` into `main` (`git merge docs/merge-conflict-exercise`).

## Conflict Output
Git halted auto-merging with:
```text
Auto-merging docs/qa-checklist.md
CONFLICT (content): Merge conflict in docs/qa-checklist.md
Automatic merge failed; fix conflicts and then commit the result.
```
The full raw conflict log and markers are preserved in [evidence/phase3/merge-conflict-output.txt](../evidence/phase3/merge-conflict-output.txt).

## Resolution Strategy
- Kept **both** factual details in one clean checklist item:
  `- [x] Backend pytest suite passes with >= 80% statement coverage (actual measured: 94%; enforced in CI via coverage.xml).`
- Removed all `<<<<<<<`, `=======`, `>>>>>>>` markers, staged `docs/qa-checklist.md`, and completed the merge commit on `main`.
- Verified `git status` clean and `git log --graph --oneline --all` intact.
