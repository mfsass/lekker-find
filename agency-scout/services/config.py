import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "masa.sqlite3"
DEFAULT_ENV_FILE = Path.home() / "OneDrive - StratHost Office 365" / "Desktop" / ".env.txt"


def load_environment() -> None:
    """Load local and external env files without copying secrets into the project."""
    load_dotenv(PROJECT_ROOT / ".env")

    explicit_env_file = os.getenv("MASA_ENV_FILE")
    env_file = Path(explicit_env_file) if explicit_env_file else DEFAULT_ENV_FILE
    if env_file.exists():
        load_dotenv(env_file)


def get_database_path() -> Path:
    configured = os.getenv("MASA_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB_PATH


def get_openrouter_api_key() -> str | None:
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_API")


def get_openrouter_model() -> str:
    return os.getenv("OPENROUTER_MODEL", "mistralai/mistral-small-3.2-24b-instruct")


def get_openrouter_fallback_model() -> str:
    return os.getenv("OPENROUTER_FALLBACK_MODEL", "qwen/qwen3-14b")


def get_openrouter_final_fallback_model() -> str:
    return os.getenv("OPENROUTER_FINAL_FALLBACK_MODEL", "openai/gpt-4.1-nano")


def get_gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


def get_gemini_model() -> str:
    # gemma-4-31b-it is the current Gemma 4 flagship via Google GenAI API
    return os.getenv("GEMINI_MODEL", "gemma-4-31b-it")


def get_sender_name() -> str:
    return os.getenv("SENDER_NAME", "Markus from Mindy Agency")


def get_sender_email() -> str:
    return os.getenv("SENDER_EMAIL", "markus@mindyagency.com")


def get_unsubscribe_base_url() -> str:
    return os.getenv("UNSUBSCRIBE_BASE_URL", "http://localhost:8000")


def get_unsubscribe_secret() -> str:
    return os.getenv("UNSUBSCRIBE_SECRET", "masa-local-dev")
