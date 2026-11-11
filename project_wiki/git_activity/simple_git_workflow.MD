# Git: Simple Feature Workflow

## The Loop

```bash
# 1. Start from an up-to-date main
git switch main

# 2. Create a branch for the feature
git switch -c feature/my-feature

# 3. Do your work, then check what changed
git status

# 4. Stage and commit (repeat as you go)
git add .
git commit -m "Describe what you added"

# 5. Merge back into main when it works
git switch main
git merge feature/my-feature

# 6. Delete the finished branch
git branch -d feature/my-feature
```

## Commands

| Step | Command | What it does |
|---|---|---|
| Branch | `git switch -c feature/name` | Creates a new branch and switches to it |
| Check | `git status` | Shows what's changed |
| Review | `git diff` | Shows the actual line changes |
| Save | `git add .` | Stages all changes |
| Save | `git commit -m "message"` | Commits the staged changes |
| Merge | `git switch main` | Goes back to the main branch |
| Merge | `git merge feature/name` | Brings the feature into main |
| Clean up | `git branch -d feature/name` | Deletes the merged branch |

## Handy Extras

| Command | What it does |
|---|---|
| `git branch` | Lists branches (current one has `*`) |
| `git log --oneline` | Shows compact commit history |
| `git restore <file>` | Discards uncommitted changes in a file (can't be undone) |
| `git stash` / `git stash pop` | Shelves unfinished work, then brings it back |

## Rules of Thumb

- Never work directly on `main`; always branch first.
- Commit small and often, with clear messages.
- Run `git status` before every commit to make sure no secrets (`.env`) are being added.