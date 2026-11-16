import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    return os.getenv(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default=0):
    try:
        return int(env(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_list(name, default=""):
    return [x.strip() for x in env(name, default).split(",") if x.strip()]
