"""Persistent configuration for RedMiner (stored at ~/.redminer/config.json)."""

import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".redminer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def _ensure_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
    """Load config from ~/.redminer/config.json. Returns empty dict if missing."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save config to ~/.redminer/config.json."""
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_cookie() -> str | None:
    """Get stored reddit_session cookie, or None."""
    return load_config().get("reddit_session")


def set_cookie(cookie: str) -> None:
    """Store reddit_session cookie persistently."""
    config = load_config()
    config["reddit_session"] = cookie
    save_config(config)


def clear_config() -> None:
    """Remove stored config."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
