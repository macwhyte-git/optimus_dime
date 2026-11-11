# pyproject.toml and `pip install -e .`

## What we did

1. Created `pyproject.toml` in the project root. It's an information sheet that tells pip the project's name, version, Python requirement, dependencies, and where the code lives (`src/`).
2. Ran `pip install -e .` from the project root with the venv active. This installed our own project into the venv in **editable** mode.

## What it does to the project

- Python can now `import bot` from anywhere in the venv, exactly like `import numpy`.
- "Editable" means the install is a pointer to `src/bot/`, not a copy. Edits to the code take effect immediately, with no reinstalling.
- The dependencies listed in `pyproject.toml` get installed along with it.
- It creates a `*.egg-info` folder in `src/`. That's harmless build metadata and is ignored by Git.

## When to run it again

| Situation | Re-run `pip install -e .`? |
|---|---|
| Editing existing code | No |
| Adding new `.py` files | No |
| Adding new subfolders inside `src/bot/` (with an `__init__.py`) | No |
| Creating a new venv (or deleting and recreating `.venv`) | **Yes** |
| Setting up the project on a new machine | **Yes** |
| Adding or changing dependencies in `pyproject.toml` | **Yes** |
| Changing the project name or version in `pyproject.toml` | **Yes** |
| Adding a new top-level package next to `bot` inside `src/` | **Yes** |
| Running `git pull` that didn't change `pyproject.toml` | No |

## Rules to remember

- `src/` must **not** have an `__init__.py`. It's a container, not a package. Every folder *inside* `src/bot/` does need one.
- Run it from the project root (the folder containing `pyproject.toml`), with `(.venv)` active.
- The dot in `pip install -e .` means "the project in this folder".
- If `pip install -e .` fails with a strange name like `__init__-0.0.0`, look for a stray `__init__.py` in `src/` or the project root.

## Quick test that it's working

```powershell
python -c "import bot; print(bot.__file__)"
```

This should print a path ending in `src\bot\__init__.py`.