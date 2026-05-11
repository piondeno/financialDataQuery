import os
from pathlib import Path
from dotenv import load_dotenv as _load_dotenv


def load_env(env_path: str | Path | None = None) -> None:
    """Load .env file. If path is None, searches standard locations."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    _load_dotenv(dotenv_path=str(env_path), override=False)


def get_config(key: str, default: str | None = None) -> str | None:
    """Read a configuration value from environment variables."""
    return os.environ.get(key, default)
