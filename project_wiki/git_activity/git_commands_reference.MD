# Git Command Reference

A quick reference for the Git commands used in this project.

---

## Setup

| Command | What it does |
|---|---|
| `git --version` | Shows the installed Git version (also confirms Git is installed) |
| `git config --global user.name "Name"` | Sets the name attached to your commits |
| `git config --global user.email "you@example.com"` | Sets the email attached to your commits |
| `git config --list` | Shows all your current Git settings |
| `git init` | Turns the current folder into a Git repository |
| `git clone <url>` | Copies an existing remote repository to your machine |

---

## Daily Workflow

| Command | What it does |
|---|---|
| `git status` | Shows changed, staged, and untracked files |
| `git add <file>` | Stages a specific file for the next commit |
| `git add .` | Stages all changes in the current folder |
| `git commit -m "message"` | Saves the staged changes as a commit with a message |
| `git commit -am "message"` | Stages and commits all *tracked* files in one step (doesn't include new files) |
| `git diff` | Shows unstaged changes line by line |
| `git diff --staged` | Shows staged changes that will go into the next commit |

Typical loop:

```bash
git status
git add .
git commit -m "Add data fetching module"
```

---

## History

| Command | What it does |
|---|---|
| `git log` | Shows the full commit history |
| `git log --oneline` | Compact one-line-per-commit history |
| `git log --oneline --graph --all` | History with a branch graph |
| `git show <commit>` | Shows the details and changes of a specific commit |
| `git blame <file>` | Shows who last changed each line of a file |

---

## Branches

| Command | What it does |
|---|---|
| `git branch` | Lists local branches (current one marked with `*`) |
| `git branch <name>` | Creates a new branch |
| `git switch <name>` | Switches to an existing branch |
| `git switch -c <name>` | Creates a new branch and switches to it |
| `git branch -M main` | Renames the current branch to `main` |
| `git merge <name>` | Merges the named branch into your current branch |
| `git branch -d <name>` | Deletes a branch that's already been merged |
| `git branch -D <name>` | Force-deletes a branch (even if unmerged) |

Older tutorials use `git checkout <name>` instead of `git switch <name>`. Both work.

---

## Undoing Things

| Command | What it does |
|---|---|
| `git restore <file>` | Discards unstaged changes in a file (**cannot be undone**) |
| `git restore --staged <file>` | Unstages a file but keeps your changes |
| `git commit --amend -m "new message"` | Rewrites the last commit message (or adds staged changes to it) |
| `git revert <commit>` | Creates a new commit that undoes a previous commit (safe for shared history) |
| `git reset --soft HEAD~1` | Undoes the last commit but keeps changes staged |
| `git reset HEAD~1` | Undoes the last commit and keeps changes unstaged |
| `git reset --hard HEAD~1` | Undoes the last commit and **deletes the changes** |
| `git clean -n` | Previews untracked files that would be deleted |
| `git clean -f` | Deletes untracked files (**cannot be undone**) |

---

## Stashing (Save Work Temporarily)

| Command | What it does |
|---|---|
| `git stash` | Shelves your uncommitted changes and gives you a clean working folder |
| `git stash list` | Lists your stashes |
| `git stash pop` | Re-applies the latest stash and removes it from the list |
| `git stash apply` | Re-applies the latest stash but keeps it in the list |
| `git stash drop` | Deletes the latest stash |

---

## Remotes (GitHub etc.)

| Command | What it does |
|---|---|
| `git remote add origin <url>` | Links your local repo to a remote repo |
| `git remote -v` | Shows the remotes linked to your repo |
| `git push -u origin main` | Pushes `main` to the remote and sets it as the default upstream |
| `git push` | Pushes your commits to the remote |
| `git pull` | Fetches and merges changes from the remote |
| `git fetch` | Downloads remote changes without merging them |

---

## Ignoring Files

| Command | What it does |
|---|---|
| `git rm -r --cached <path>` | Stops tracking a file/folder that's already been committed, but keeps it on disk (use after adding it to `.gitignore`) |
| `git check-ignore -v <file>` | Shows which `.gitignore` rule is ignoring a file |

---

## Tags

| Command | What it does |
|---|---|
| `git tag v1.0` | Marks the current commit with a label (e.g. a release) |
| `git tag` | Lists all tags |
| `git push origin v1.0` | Pushes a tag to the remote |

---

## Safety Notes

- **Commit often** with clear messages. Small commits are easy to undo.
- **Never commit secrets** (API keys, `.env`). If you commit one by accident, treat the key as compromised and regenerate it, since deleting it in a later commit doesn't remove it from history.
- Commands marked **cannot be undone** (`restore`, `reset --hard`, `clean -f`) permanently discard work. Run `git status` and `git diff` first.