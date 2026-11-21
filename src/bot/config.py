"""Configuration loader: reads job settings from the YAML files in config/.

This module only FINDS and READS settings. It does not know what any setting
means; that is each job's business. One shared loader means the finding and
reading logic exists once, so a fix to it fixes every job.

Secrets (database URL, API keys) are NOT loaded here; they stay in .env.
"""

from pathlib import Path

import yaml

# --- Section 1: where the config files live ---------------------------------

# This file is <project>/src/bot/config.py. parents[0] is src/bot, parents[1]
# is src, and parents[2] is the project root. The path is built from this
# file's OWN location (__file__), not from the folder Python was started in,
# so it works the same from a terminal, a script or a scheduled task.
# Caveat: this assumes the file stays at src/bot/config.py. If it moves
# deeper, the number in parents[2] must change.
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


# --- Section 2: turning a name or a path into a file ------------------------

def resolve_config_path(name_or_path) -> Path:
    """Work out which file a caller means.

    "collector"                -> <project>/config/collector.yaml
    "config/collector_eth.yaml" -> that exact file (relative paths are
                                   relative to where Python was started)

    Anything ending in .yaml or .yml is treated as a path; anything else is a
    job name. This lets the same function serve both the everyday case (a
    name) and the --config command-line override (a path).
    """
    path = Path(name_or_path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return path.resolve()
    return CONFIG_DIR / f"{name_or_path}.yaml"


# --- Section 3: reading a file ----------------------------------------------

def load_config(name_or_path) -> dict:
    """Read one YAML file and return its settings as a dictionary.

    Each call reads the file again and returns a fresh dictionary, so one
    script changing a value cannot affect another. Scripts should call this
    once at start-up and pass the values down as arguments.

    yaml.safe_load only builds plain data (dicts, lists, text, numbers,
    booleans) and cannot run code, which is why it is the safe way to read
    config files.
    """
    path = resolve_config_path(name_or_path)
    if not path.is_file():
        # Say exactly which path was tried: a wrong name or a wrong working
        # folder are the two usual causes.
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # An empty file loads as None, and a file that is just a list loads as a
    # list. Neither is usable as settings, so fail now with a clear message.
    if not isinstance(data, dict):
        raise ValueError(
            f"Config file {path} must contain settings written as 'key: value', "
            f"but it loaded as {type(data).__name__}"
        )
    return data


# --- Section 4: checking that required settings are present -----------------

def require_keys(settings: dict, required: list[str], source: str = "config") -> None:
    """Fail immediately, naming every missing setting, if any are absent.

    Without this, a missing setting only shows up later as a KeyError deep
    inside the job, naming the key but not which file it should be in. Calling
    this at start-up turns that into one clear message listing everything
    that is missing, so the mistake is fixed in one go.
    """
    missing = [key for key in required if key not in settings]
    if missing:
        raise ValueError(f"Missing settings in {source}: {', '.join(missing)}")